# -*- coding: utf-8 -*-
# Copyright: 2009 Nadia Alramli
# License: BSD
"""Draws an animated terminal progress bar
Usage:
    p = ProgressBar("blue")
    p.render(percentage, message)
"""

import sys
import time as timemod
import ModColor


def disableBars():
    ProgressBar.silent = 1


def test():
    pBAR = ProgressBar(
        'white',
        width=50,
        block='=',
        empty=' ',
        Title="Solving ",
        HeaderSize=10,
     TitleSize=13)
    nt = 10
    for NDone in xrange(nt):
        f = int(100.*NDone/float(nt-1))
        pBAR.render(f, '%4i/%i' % (NDone, nt-1))
        timemod.sleep(0.2)


class ProgressBar(object):
    """Terminal progress bar class"""
    #TEMPLATE = ('  %(title)s %(percent)3.2i%% [%(color)s%(progress)s%(normal)s%(empty)s] %(message)s\n')
    #TEMPLATE = ('  %(message)s [%(color)s%(progress)s%(normal)s%(empty)s] %(percent)3.2i%% \n')
    #TEMPLATE = ('  %(header)s [%(color)s%(progress)s%(normal)s%(empty)s] %(percent)3.2i%% %(time)s \n')
    TEMPLATE = (
        '  %(title)s%(header)s [%(color)s%(progress)s%(normal)s%(empty)s] %(percent)3.2i%% %(time)s \n')

    PADDING = 7
    silent = 0

    def __init__(
        self,
        color=None,
        width=30,
        block='█',
        empty=' ',
        Title=None,
        HeaderSize=40,
     TitleSize=30):
        """
        color -- color name (BLUE GREEN CYAN RED MAGENTA YELLOW WHITE BLACK)
        width -- bar width (optinal)
        block -- progress display character (default '█')
        empty -- bar display character (default ' ')
        """

        if self.silent == 1:
            return

        import terminal
        if color:
            self.color = getattr(terminal, color.upper())
        else:
            self.color = ''
        if width and width < terminal.getValueChecked("COLUMNS") - self.PADDING:
            self.width = width
        else:
            # Adjust to the width of the terminal
            self.width = terminal.getValueChecked("COLUMNS") - self.PADDING
        self.block = block
        self.empty = empty
        self.progress = None
        self.lines = 0
        self.TitleSize = TitleSize
        Title = ModColor.Str(Title, col="blue", Bold=False)
        self.TitleIn = Title
        self.Title = Title  # self.format(Title,self.TitleSize)

        self.HasRendered = False
        self.t0 = None
        self.HeaderSize = HeaderSize
        self.disableTag = False

    def format(self, strin, Size, side=0, TitleIn=None):
        if TitleIn is None:
            Title = self.TitleIn
        else:
            Title = TitleIn

        if len(strin) > Size:
            return strin[0:Size]
        if side == 0:
            strin = strin+" "+"."*(Size-len(strin))
        if side == 1:
            strin = "."*(Size-len(strin))+" "+strin
        if side == 2:
            strin = "%s %s %s" % (
                Title, "."*(Size-len(self.TitleIn)-len(strin)), strin)
        return strin

    def disable(self):
        self.disableTag = True

    def GiveStrMinSec(self):
        t1 = timemod.time()
        dt = t1-self.t0
        ss = (dt)/60.
        m = int(ss)
        s = int((ss-m)*60.)
        return " - %i%s%2.2i%s" % (m, "'", s, '"')

    def reset(self):
        # print
        # "RESET!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        self.HasRendered = False
        self.t0 = None
        self.progress = None

    def render(self, percent, message='', PutTime=True):
        """Print the progress bar
        percent -- the progress percentage %
        message -- message string (optional)
        """
        if self.silent == 1:
            return
        if self.disableTag:
            return
        import terminal

        if (self.Title is not None) & (self.HasRendered == False):
            # print
            # print "  %s"%self.Title
            self.HasRendered = True

        if self.t0 is None:
            self.t0 = timemod.time()

        StrTime = ""
        if PutTime:
            StrTime = self.GiveStrMinSec()

        inline_msg_len = 0
        if message:
            # The length of the first line in the message
            inline_msg_len = len(message.splitlines()[0])+len(self.Title)

        if inline_msg_len + self.width + \
                self.PADDING > terminal.getValueChecked("COLUMNS"):
            # The message is too long to fit in one line.
            # Adjust the bar width to fit.
            bar_width = terminal.getValueChecked(
                "COLUMNS") - inline_msg_len - self.PADDING
        else:
            bar_width = self.width

        # Check if render is called for the first time
        if self.progress is not None:
            self.clear()
        self.progress = (bar_width * percent) / 100

        DicoData = {
            'title': self.Title,
            'percent': percent,
            'color': self.color,
            'progress': self.block * self.progress,
            'normal': terminal.NORMAL,
            'empty': self.empty * (bar_width - self.progress),
            'message': message,
            'time': StrTime,
            'header': self.format(message, self.HeaderSize, 1, TitleIn="")
        }
        data = self.TEMPLATE % DicoData
        # print DicoData
        # print data
        # stop
        sys.stdout.write(data)
        sys.stdout.flush()
        # The number of lines printed
        self.lines = len(data.splitlines())

    def clear(self):
        """Clear all printed lines"""

        import terminal
        sys.stdout.write(
            self.lines * (terminal.UP + terminal.BOL + terminal.CLEAR_EOL)
        )
