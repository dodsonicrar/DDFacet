from DDFacet.ToolsDir import ModFFTW
import numpy as np
import random
from deap import tools
import pylab
from mpl_toolkits.axes_grid1 import make_axes_locatable
from DDFacet.Other import ClassTimeIt
from itertools import repeat
from DDFacet.ToolsDir import ClassSpectralFunctions


class ClassParamMachine():
    def __init__(self,ListPixParms,ListPixData,FreqsInfo,SolveParam=["S","Alpha"]):

        self.ListPixParms=ListPixParms
        self.ListPixData=ListPixData
        self.NPixListParms=len(self.ListPixParms)
        self.NPixListData=len(self.ListPixData)

        self.SolveParam=SolveParam

        self.MultiFreqMode=False
        if "Alpha" in self.SolveParam:
            self.MultiFreqMode=True

        self.NParam=len(self.SolveParam)

        self.DicoIParm={}
        DefaultValues={"S":{"Mean":0.,
                            "Sigma":{
                                "Type":"PeakFlux",
                                "Value":0.001}
                        },
                       "Alpha":{"Mean":-0.6,
                                "Sigma":{
                                    "Type":"Abs",
                                    "Value":0.1}
                                }
                   }

        for Type in DefaultValues.keys():
            self.DicoIParm[Type]={}
            self.DicoIParm[Type]["Default"]=DefaultValues[Type]
            self.DicoIParm[Type]["iSlice"]=None
            
        for iParm,Type in zip(range(self.NParam),self.SolveParam):
            self.DicoIParm[Type]["iSlice"]=iParm

        self.NFreqBands=len(FreqsInfo["freqs"])
        self.SetSquareGrids()

    def setFreqs(self,DicoMappingDesc):
        self.DicoMappingDesc=DicoMappingDesc
        if self.DicoMappingDesc==None: return
        self.SpectralFunctionsMachine=ClassSpectralFunctions.ClassSpectralFunctions(self.DicoMappingDesc)#,BeamEnable=False)
        

    def GiveInitList(self,toolbox):
        ListPars=[]
        for Type in self.SolveParam:
            DicoSigma=self.DicoIParm[Type]["Default"]["Sigma"]
            MeanVal=self.DicoIParm[Type]["Default"]["Mean"]
            if Type=="S":
                toolbox.register("attr_float_unif_S", random.uniform, 0., 0.1)
                ListPars+=[toolbox.attr_float_unif_S]*self.NPixListParms
            if Type=="Alpha":
                toolbox.register("attr_float_normal_Alpha", random.gauss, MeanVal, 0)#DicoSigma["Value"])
                ListPars+=[toolbox.attr_float_normal_Alpha]*self.NPixListParms
        return ListPars

    def ReinitPop(self,pop,SModelArray,AlphaModel=None):

        for Type in self.SolveParam:
            DicoSigma=self.DicoIParm[Type]["Default"]["Sigma"]
            MeanVal=self.DicoIParm[Type]["Default"]["Mean"]
            if DicoSigma["Type"]=="Abs":
                SigVal=DicoSigma["Value"]
            elif DicoSigma["Type"]=="PeakFlux":
                SigVal=DicoSigma["Value"]*np.max(np.abs(SModelArray))
            

            for i_indiv,indiv in zip(range(len(pop)),pop):
                SubArray=self.ArrayToSubArray(indiv,Type=Type)
                if Type=="S":
                    SubArray[:]=SModelArray[:]
                    if i_indiv!=0: 
                        SubArray[:]+=np.random.randn(SModelArray.size)*SigVal
                if Type=="Alpha":
                    if AlphaModel==None:
                        AlphaModel=MeanVal*np.ones((SModelArray.size,),np.float32)
                    SubArray[:]=AlphaModel[:]
                    if i_indiv!=0: 
                        SubArray[:]+=np.random.randn(SModelArray.size)*SigVal

                    # SubArray[:]=np.zeros_like(AlphaModel)[:]#+np.random.randn(SModelArray.size)*SigVal
                    # print SubArray[:]




            
    def ArrayToSubArray(self,A,Type):
        iSlice=self.DicoIParm[Type]["iSlice"]
        if iSlice!=None:
            ParmsArray=A.reshape((self.NParam,self.NPixListParms))[iSlice]
        elif "DataModel" in self.DicoIParm[Type].keys():
            ParmsArray=self.DicoIParm[Type]["DataModel"].flatten().copy()
        else:
            ParmsArray=np.zeros((self.NPixListParms,),np.float32)
            ParmsArray.fill(self.DicoIParm[Type]["Default"]["Mean"])

        return ParmsArray

    # def SubArrayToArray(self,A,Type):
    #     iSlice=self.DicoIParm[Type]["iSlice"]
    #     if iSlice!=None:
    #         ParmsArray=A.reshape((self.NParam,self.AM.NPixListParms))[iSlice]
    #     else:
    #         ParmsArray=np.zeros((self.AM.NPixListParm,),np.float32)
    #         ParmsArray.fill(self.DicoIParm[Type]["Default"])

    #     return ParmsArray

    def SetSquareGrid(self,Type):
        if Type=="Data":
            ArrayPix=np.array(self.ListPixData)
        else:
            ArrayPix=np.array(self.ListPixParms)

        x,y=ArrayPix.T
        nx=x.max()-x.min()+1
        ny=y.max()-y.min()+1
        NPixSquare=np.max((nx,ny))
        xx,yy=np.mgrid[0:NPixSquare,0:NPixSquare]

        MappingIndexToXYPix=(xx[x-x.min(),y-y.min()],yy[x-x.min(),y-y.min()])
        xx=np.int32(xx.flatten())
        yy=np.int32(yy.flatten())
        return {"XY":(xx,yy),
                "NPixSquare":NPixSquare,
                "ArrayPix":ArrayPix,
                "MappingIndexToXYPix":MappingIndexToXYPix,
                "x0y0":(x.min(),y.min())}

    def SetSquareGrids(self):
        self.SquareGrids={"Data":self.SetSquareGrid("Data"),
                          "Parms":self.SetSquareGrid("Parms")}

    # def IndToArray(self,V,key=None):
    #     A=np.zeros((1,1,nx,nx),np.float32)
    #     A.ravel()[:]=np.array(V).ravel()[:]
    #     return A
    
    # def ArrayToInd(self,A):
    #     return A.ravel()#.tolist()

    def ModelToSquareArray(self,Ain,TypeInOut=("Parms","Data"),DomainOut="Freqs"):

        TypeIn,TypeOut=TypeInOut

        if DomainOut=="Parms":
            NSlice=self.NParam
        elif DomainOut=="Freqs":
            NSlice=self.NFreqBands

        NPixSquare=self.SquareGrids[TypeOut]["NPixSquare"]
        A=np.zeros((NSlice,1,NPixSquare,NPixSquare),Ain.dtype)
        x0y0_in  = self.SquareGrids[TypeIn]["x0y0"]
        x0y0_out = self.SquareGrids[TypeOut]["x0y0"]
        dx=x0y0_in[0]-x0y0_out[0]
        dy=x0y0_in[1]-x0y0_out[1]

        ArrayPix=self.SquareGrids[TypeIn]["ArrayPix"]

        Ain=Ain.reshape((NSlice,Ain.size/NSlice))

        x,y=ArrayPix.T
        #print "=============",TypeInOut,A.shape,Ain.shape
        #print "before",A
        xpos=x-x.min()+dx
        ypos=y-y.min()+dy
        nch,npol,nx,_=A.shape
        for iSlice in range(NSlice):
            
            #A[iChannel,0][xpos,ypos]=Ain[iChannel,0]#.copy().flatten()[:]
            ind=xpos*nx + ypos
            A[iSlice].flat[ind]=Ain[iSlice].flat[:]

            # print "ichannel:",iSlice
            # print "in  ",Ain[iSlice].ravel()
            # print "out ",A[iSlice,0,xpos,ypos]
            # R=Ain[iSlice].ravel()-A[iSlice,0,xpos,ypos]
            # print "diff",R
            # if np.max(R)!=0: stop

        return A

    def SquareArrayToModel(self,A,TypeInOut=("Data","Parms")):
        TypeIn,TypeOut=TypeInOut
        x0y0_in  = self.SquareGrids[TypeIn]["x0y0"]
        x0y0_out = self.SquareGrids[TypeOut]["x0y0"]
        dx=x0y0_in[0]-x0y0_out[0]
        dy=x0y0_in[1]-x0y0_out[1]
        if TypeOut=="Data":
            NPixOut=self.NPixListData
        else:
            NPixOut=self.NPixListParms
        
        ArrayPix=self.SquareGrids[TypeOut]["ArrayPix"]
        x,y=ArrayPix.T

        ArrayModel=A[:,0,x-x.min()-dx,y-y.min()+dy].ravel()

        return ArrayModel
        

    def GiveModelArray(self,A):
        
        MA=np.zeros((self.NFreqBands,self.NPixListParms),np.float32)

        S=self.ArrayToSubArray(A,"S")
        Alpha=self.ArrayToSubArray(A,"Alpha")

        self.MultiFreqMode=True
        for iBand in range(self.NFreqBands):
            if self.MultiFreqMode:
                MA[iBand]=self.SpectralFunctionsMachine.IntExpFunc(S0=S,Alpha=Alpha,iChannel=iBand,iFacet=0)
            else:
                MA[iBand]=S[:]
            #Alpha=self.ParmToArray(A,"Alpha")


        return MA
