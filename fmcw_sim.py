#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: LFMCW Radar Simulation
# Author: Ben Cometto
# GNU Radio version: 3.10.10.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import zeromq
import numpy as np
import sip



class fmcw_sim(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "LFMCW Radar Simulation", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("LFMCW Radar Simulation")
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

        self.settings = Qt.QSettings("GNU Radio", "fmcw_sim")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = int(200e6)
        self.max_freq = max_freq = samp_rate*0.95
        self.t_chirp = t_chirp = 0.000005
        self.min_freq = min_freq = -max_freq
        self.c = c = 300000000
        self.max_distance = max_distance = min(30,t_chirp*c)
        self.alpha = alpha = (max_freq-min_freq)/t_chirp
        self.max_fbeat = max_fbeat = max_distance*2*alpha/c
        self.distance_m = distance_m = 100
        self.k_bins = k_bins = 2**14
        self.delay_time = delay_time = 2*distance_m/c
        self.decimation = decimation = round(samp_rate/max_fbeat)
        self.reflection_amplitude = reflection_amplitude = 0.75
        self.f_b_ideal = f_b_ideal = 2*distance_m*alpha/c
        self.distance_per_sample = distance_per_sample = c/samp_rate
        self.distance_max_m = distance_max_m = 200
        self.df = df = samp_rate/k_bins
        self.delay_samples = delay_samples = int(delay_time*samp_rate)
        self.dec_lpf_taps = dec_lpf_taps = firdes.low_pass(1.0, samp_rate, int(samp_rate/decimation),samp_rate*0.1, window.WIN_HAMMING, 6.76)

        ##################################################
        # Blocks
        ##################################################

        self.zeromq_pub_sink_0 = zeromq.pub_sink(gr.sizeof_gr_complex, 1, 'tcp://localhost:4444', 100, False, (-1), '', True, True)
        self.qtgui_freq_sink_x_0_0 = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Demodulated Signal", #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0_0.enable_grid(False)
        self.qtgui_freq_sink_x_0_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_0_0_win)
        self.fir_filter_xxx_0 = filter.fir_filter_ccc(decimation, dec_lpf_taps)
        self.fir_filter_xxx_0.declare_sample_delay(0)
        self._distance_m_range = qtgui.Range(0, distance_max_m, 0.25, 100, 200)
        self._distance_m_win = qtgui.RangeWidget(self._distance_m_range, self.set_distance_m, "Object Distance", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._distance_m_win)
        self.blocks_vco_c_0 = blocks.vco_c(samp_rate, (2*np.pi), 1)
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_float*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_multiply_const_vxx_2 = blocks.multiply_const_cc(reflection_amplitude)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff(((max_freq-min_freq)))
        self.blocks_multiply_conjugate_cc_0 = blocks.multiply_conjugate_cc(1)
        self.blocks_delay_0 = blocks.delay(gr.sizeof_gr_complex*1, delay_samples)
        self.blocks_add_const_vxx_0 = blocks.add_const_ff(min_freq)
        self.analog_sig_source_x_0 = analog.sig_source_f(samp_rate, analog.GR_SAW_WAVE, (1/t_chirp), 1, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_add_const_vxx_0, 0), (self.blocks_vco_c_0, 0))
        self.connect((self.blocks_delay_0, 0), (self.blocks_multiply_const_vxx_2, 0))
        self.connect((self.blocks_multiply_conjugate_cc_0, 0), (self.fir_filter_xxx_0, 0))
        self.connect((self.blocks_multiply_conjugate_cc_0, 0), (self.qtgui_freq_sink_x_0_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_add_const_vxx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_2, 0), (self.blocks_multiply_conjugate_cc_0, 1))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_vco_c_0, 0), (self.blocks_delay_0, 0))
        self.connect((self.blocks_vco_c_0, 0), (self.blocks_multiply_conjugate_cc_0, 0))
        self.connect((self.fir_filter_xxx_0, 0), (self.zeromq_pub_sink_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "fmcw_sim")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_dec_lpf_taps(firdes.low_pass(1.0, self.samp_rate, int(self.samp_rate/self.decimation), self.samp_rate*0.1, window.WIN_HAMMING, 6.76))
        self.set_decimation(round(self.samp_rate/self.max_fbeat))
        self.set_delay_samples(int(self.delay_time*self.samp_rate))
        self.set_df(self.samp_rate/self.k_bins)
        self.set_distance_per_sample(self.c/self.samp_rate)
        self.set_max_freq(self.samp_rate*0.95)
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.qtgui_freq_sink_x_0_0.set_frequency_range(0, self.samp_rate)

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
        self.set_max_distance(min(30,self.t_chirp*self.c))
        self.analog_sig_source_x_0.set_frequency((1/self.t_chirp))

    def get_min_freq(self):
        return self.min_freq

    def set_min_freq(self, min_freq):
        self.min_freq = min_freq
        self.set_alpha((self.max_freq-self.min_freq)/self.t_chirp)
        self.blocks_add_const_vxx_0.set_k(self.min_freq)
        self.blocks_multiply_const_vxx_0.set_k(((self.max_freq-self.min_freq)))

    def get_c(self):
        return self.c

    def set_c(self, c):
        self.c = c
        self.set_delay_time(2*self.distance_m/self.c)
        self.set_distance_per_sample(self.c/self.samp_rate)
        self.set_f_b_ideal(2*self.distance_m*self.alpha/self.c)
        self.set_max_distance(min(30,self.t_chirp*self.c))
        self.set_max_fbeat(self.max_distance*2*self.alpha/self.c)

    def get_max_distance(self):
        return self.max_distance

    def set_max_distance(self, max_distance):
        self.max_distance = max_distance
        self.set_max_fbeat(self.max_distance*2*self.alpha/self.c)

    def get_alpha(self):
        return self.alpha

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.set_f_b_ideal(2*self.distance_m*self.alpha/self.c)
        self.set_max_fbeat(self.max_distance*2*self.alpha/self.c)

    def get_max_fbeat(self):
        return self.max_fbeat

    def set_max_fbeat(self, max_fbeat):
        self.max_fbeat = max_fbeat
        self.set_decimation(round(self.samp_rate/self.max_fbeat))

    def get_distance_m(self):
        return self.distance_m

    def set_distance_m(self, distance_m):
        self.distance_m = distance_m
        self.set_delay_time(2*self.distance_m/self.c)
        self.set_f_b_ideal(2*self.distance_m*self.alpha/self.c)

    def get_k_bins(self):
        return self.k_bins

    def set_k_bins(self, k_bins):
        self.k_bins = k_bins
        self.set_df(self.samp_rate/self.k_bins)

    def get_delay_time(self):
        return self.delay_time

    def set_delay_time(self, delay_time):
        self.delay_time = delay_time
        self.set_delay_samples(int(self.delay_time*self.samp_rate))

    def get_decimation(self):
        return self.decimation

    def set_decimation(self, decimation):
        self.decimation = decimation
        self.set_dec_lpf_taps(firdes.low_pass(1.0, self.samp_rate, int(self.samp_rate/self.decimation), self.samp_rate*0.1, window.WIN_HAMMING, 6.76))

    def get_reflection_amplitude(self):
        return self.reflection_amplitude

    def set_reflection_amplitude(self, reflection_amplitude):
        self.reflection_amplitude = reflection_amplitude
        self.blocks_multiply_const_vxx_2.set_k(self.reflection_amplitude)

    def get_f_b_ideal(self):
        return self.f_b_ideal

    def set_f_b_ideal(self, f_b_ideal):
        self.f_b_ideal = f_b_ideal

    def get_distance_per_sample(self):
        return self.distance_per_sample

    def set_distance_per_sample(self, distance_per_sample):
        self.distance_per_sample = distance_per_sample

    def get_distance_max_m(self):
        return self.distance_max_m

    def set_distance_max_m(self, distance_max_m):
        self.distance_max_m = distance_max_m

    def get_df(self):
        return self.df

    def set_df(self, df):
        self.df = df

    def get_delay_samples(self):
        return self.delay_samples

    def set_delay_samples(self, delay_samples):
        self.delay_samples = delay_samples
        self.blocks_delay_0.set_dly(int(self.delay_samples))

    def get_dec_lpf_taps(self):
        return self.dec_lpf_taps

    def set_dec_lpf_taps(self, dec_lpf_taps):
        self.dec_lpf_taps = dec_lpf_taps
        self.fir_filter_xxx_0.set_taps(self.dec_lpf_taps)




def main(top_block_cls=fmcw_sim, options=None):

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
