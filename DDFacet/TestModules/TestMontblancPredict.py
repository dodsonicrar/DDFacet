import os
import unittest
import shutil
import subprocess

import numpy as np

from DDFacet.Parset.ReadCFG import Parset

def run_ddf(parset, image_prefix, stdout_filename, stderr_filename):
    """ Execute DDFacet """
    args = ['DDF.py', parset,
        '--ImageName=%s' % image_prefix]

    stdout_file = open(stdout_filename, 'w')
    stderr_file = open(stderr_filename, 'w')

    with stdout_file, stderr_file:
        subprocess.check_call(args, env=os.environ.copy(),
            stdout=stdout_file, stderr=stderr_file)

class TestMontblancPredict(unittest.TestCase):

    def testMontblancPredict(self):
        pc = self._parset.Config

        # Set the image name prefix
        pc.set("Images", "ImageName", self._image_prefix)

        # Configure DDFacet to predict using Montblanc
        pc.set("ImagerGlobal", "Mode", "Predict")
        pc.set("ImagerGlobal", "PredictMode", "Montblanc")

        # Predict from Predict.DicoModel
        pc.set("Images", "PredictModelName", os.path.join(self._input_dir,
            "sky_models", "Predict.DicoModel"))

        # Predict into MONTBLANC_DATA
        pc.set("VisData", "MSName", os.path.join(self._input_dir,
            "basicSSMFClean.MS_p0"))
        pc.set("VisData", "PredictColName", "MONTBLANC_DATA")

        # Write the parset config to the output file name
        with open(self._output_parset_filename, 'w') as op:
            pc.write(op)

        # Run DDFacet
        run_ddf(self._output_parset_filename, self._image_prefix,
            self._stdout_filename, self._stderr_filename)

    def testDDFacetPredict(self):
        pc = self._parset.Config

        # Set the image name prefix
        pc.set("Images", "ImageName", self._image_prefix)

        # Configure DDFacet to predict using DDFacet's DeGridder
        pc.set("ImagerGlobal", "Mode", "Predict")
        pc.set("ImagerGlobal", "PredictMode", "DeGridder")

        # Predict from Predict.DicoModel
        pc.set("Images", "PredictModelName", os.path.join(self._input_dir,
            "sky_models", "Predict.DicoModel"))

        # Predict into DDFACET_DATA
        pc.set("VisData", "MSName", os.path.join(self._input_dir,
            "basicSSMFClean.MS_p0"))
        pc.set("VisData", "PredictColName", "DDFACET_DATA")

        # Write the parset config to the output file name
        with open(self._output_parset_filename, 'w') as op:
            pc.write(op)

        # Run DDFacet
        run_ddf(self._output_parset_filename, self._image_prefix,
            self._stdout_filename, self._stderr_filename)

    def setUp(self):
        cname = self.__class__.__name__
        self._input_dir = os.getenv('DDFACET_TEST_DATA_DIR', '/') + "/"
        self._output_dir = os.getenv('DDFACET_TEST_OUTPUT_DIR', '/tmp/') + "/"
        self._image_prefix = ''.join((self._output_dir, cname, ".run"))
        self._input_parset_filename = ''.join((self._input_dir, cname, '.parset.cfg'))
        self._output_parset_filename = ''.join((self._output_dir, cname, '.run.parset.cfg'))
        self._stdout_filename = ''.join((self._output_dir, cname, ".run.out.log"))
        self._stderr_filename = ''.join((self._output_dir, cname, ".run.err.log"))

        if not os.path.isfile(self._input_parset_filename):
            raise RuntimeError("Parset file %s does not exist" % self._input_parset_filename)

        self._parset = Parset(File=self._input_parset_filename)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()