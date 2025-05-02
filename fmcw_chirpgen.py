#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: LFMCW Radar Chirp Generator
# Author: Ben Cometto
# GNU Radio version: 3.10.10.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import numpy as np



class fmcw_chirpgen(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "LFMCW Radar Chirp Generator", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("LFMCW Radar Chirp Generator")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "fmcw_chirpgen")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = int(4e6)
        self.max_freq = max_freq = samp_rate*0.4
        self.t_chirp = t_chirp = 0.00004
        self.min_freq = min_freq = -max_freq
        self.chirp_length_s = chirp_length_s = 1
        self.c = c = 300000000
        self.alpha = alpha = (max_freq-min_freq)/t_chirp

        ##################################################
        # Blocks
        ##################################################

        self.blocks_vco_c_0 = blocks.vco_c(samp_rate, (2*np.pi), 1)
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_float*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff(((max_freq-min_freq)))
        self.blocks_head_0 = blocks.head(gr.sizeof_gr_complex*1, (chirp_length_s*samp_rate))
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, 'C:\\workspace\\ece448_fmcw\\chirps\\chirp2.dat', False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_add_const_vxx_0 = blocks.add_const_ff(min_freq)
        self.analog_sig_source_x_0 = analog.sig_source_f(samp_rate, analog.GR_SAW_WAVE, (1/t_chirp), 1, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_add_const_vxx_0, 0), (self.blocks_vco_c_0, 0))
        self.connect((self.blocks_head_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_add_const_vxx_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_vco_c_0, 0), (self.blocks_head_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "fmcw_chirpgen")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_max_freq(self.samp_rate*0.4)
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.blocks_head_0.set_length((self.chirp_length_s*self.samp_rate))
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)

    def get_max_freq(self):
        return self.max_freq

    def set_max_freq(self, max_freq):
        self.max_freq = max_freq
        self.set_alpha((self.max_freq-self.min_freq)/self.t_chirp)
        self.set_min_freq(-self.max_freq)
        self.blocks_multiply_const_vxx_0.set_k(((self.max_freq-self.min_freq)))

    def get_t_chirp(self):
        return self.t_chirp

    def set_t_chirp(self, t_chirp):
        self.t_chirp = t_chirp
        self.set_alpha((self.max_freq-self.min_freq)/self.t_chirp)
        self.analog_sig_source_x_0.set_frequency((1/self.t_chirp))

    def get_min_freq(self):
        return self.min_freq

    def set_min_freq(self, min_freq):
        self.min_freq = min_freq
        self.set_alpha((self.max_freq-self.min_freq)/self.t_chirp)
        self.blocks_add_const_vxx_0.set_k(self.min_freq)
        self.blocks_multiply_const_vxx_0.set_k(((self.max_freq-self.min_freq)))

    def get_chirp_length_s(self):
        return self.chirp_length_s

    def set_chirp_length_s(self, chirp_length_s):
        self.chirp_length_s = chirp_length_s
        self.blocks_head_0.set_length((self.chirp_length_s*self.samp_rate))

    def get_c(self):
        return self.c

    def set_c(self, c):
        self.c = c

    def get_alpha(self):
        return self.alpha

    def set_alpha(self, alpha):
        self.alpha = alpha




def main(top_block_cls=fmcw_chirpgen, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
