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
from gnuradio import blocks
import pmt
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import uhd
import time
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
        self.samp_rate = samp_rate = int(4e6)
        self.max_freq = max_freq = samp_rate*0.4
        self.t_chirp = t_chirp = 0.00004
        self.min_freq = min_freq = -max_freq
        self.k_bins = k_bins = 2**19
        self.c = c = 300000000
        self.radio_tx_gain = radio_tx_gain = 20
        self.radio_rx_gain = radio_rx_gain = 36
        self.radio_center = radio_center = 1e9
        self.min_buffer = min_buffer = 1000
        self.max_buffer = max_buffer = 8192
        self.distance_per_sample = distance_per_sample = c/samp_rate/2
        self.distance_max_m = distance_max_m = 100
        self.df = df = samp_rate/k_bins
        self.calibration_delay = calibration_delay = 0
        self.alpha = alpha = (max_freq-min_freq)/t_chirp

        ##################################################
        # Blocks
        ##################################################

        self._calibration_delay_range = qtgui.Range(0, 800, 1, 0, 200)
        self._calibration_delay_win = qtgui.RangeWidget(self._calibration_delay_range, self.set_calibration_delay, "'calibration_delay'", "counter_slider", int, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._calibration_delay_win)
        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        _last_pps_time = self.uhd_usrp_source_0.get_time_last_pps().get_real_secs()
        # Poll get_time_last_pps() every 50 ms until a change is seen
        while(self.uhd_usrp_source_0.get_time_last_pps().get_real_secs() == _last_pps_time):
            time.sleep(0.05)
        # Set the time to PC time on next PPS
        self.uhd_usrp_source_0.set_time_next_pps(uhd.time_spec(int(time.time()) + 1.0))
        # Sleep 1 second to ensure next PPS has come
        time.sleep(1)

        self.uhd_usrp_source_0.set_center_freq(radio_center, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_gain(radio_rx_gain, 0)
        self.uhd_usrp_source_0.set_min_output_buffer(min_buffer)
        self.uhd_usrp_source_0.set_max_output_buffer(max_buffer)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
            "",
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        _last_pps_time = self.uhd_usrp_sink_0.get_time_last_pps().get_real_secs()
        # Poll get_time_last_pps() every 50 ms until a change is seen
        while(self.uhd_usrp_sink_0.get_time_last_pps().get_real_secs() == _last_pps_time):
            time.sleep(0.05)
        # Set the time to PC time on next PPS
        self.uhd_usrp_sink_0.set_time_next_pps(uhd.time_spec(int(time.time()) + 1.0))
        # Sleep 1 second to ensure next PPS has come
        time.sleep(1)

        self.uhd_usrp_sink_0.set_center_freq(radio_center, 0)
        self.uhd_usrp_sink_0.set_antenna("TX/RX", 0)
        self.uhd_usrp_sink_0.set_gain(radio_tx_gain, 0)
        self.uhd_usrp_sink_0.set_min_output_buffer(min_buffer)
        self.uhd_usrp_sink_0.set_max_output_buffer(max_buffer)
        self.qtgui_number_sink_0_0 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_0.set_update_time(0.10)
        self.qtgui_number_sink_0_0.set_title("object distance")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_0.set_min(i, 0)
            self.qtgui_number_sink_0_0.set_max(i, distance_max_m)
            self.qtgui_number_sink_0_0.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_0.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_0.set_label(i, labels[i])
            self.qtgui_number_sink_0_0.set_unit(i, units[i])
            self.qtgui_number_sink_0_0.set_factor(i, factor[i])

        self.qtgui_number_sink_0_0.enable_autoscale(False)
        self._qtgui_number_sink_0_0_win = sip.wrapinstance(self.qtgui_number_sink_0_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_0_win)
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
        self.fft_vxx_0_0 = fft.fft_vcc(k_bins, True, window.blackmanharris(k_bins), False, 2)
        self.blocks_stream_to_vector_0_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, k_bins)
        self.blocks_short_to_float_0 = blocks.short_to_float(1, 1)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_short*1)
        self.blocks_multiply_const_vxx_1_0 = blocks.multiply_const_ff((c/2/alpha))
        self.blocks_multiply_const_vxx_1 = blocks.multiply_const_ff((1*df))
        self.blocks_multiply_conjugate_cc_0 = blocks.multiply_conjugate_cc(1)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_gr_complex*1, 'C:\\workspace\\ece448_fmcw\\chirps\\chirp2.dat', True, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_delay_0 = blocks.delay(gr.sizeof_gr_complex*1, calibration_delay)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(k_bins)
        self.blocks_argmax_xx_1 = blocks.argmax_fs(k_bins)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_argmax_xx_1, 1), (self.blocks_null_sink_0, 0))
        self.connect((self.blocks_argmax_xx_1, 0), (self.blocks_short_to_float_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_argmax_xx_1, 0))
        self.connect((self.blocks_delay_0, 0), (self.blocks_multiply_conjugate_cc_0, 0))
        self.connect((self.blocks_file_source_0, 0), (self.blocks_delay_0, 0))
        self.connect((self.blocks_file_source_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.blocks_multiply_conjugate_cc_0, 0), (self.blocks_stream_to_vector_0_0, 0))
        self.connect((self.blocks_multiply_conjugate_cc_0, 0), (self.qtgui_freq_sink_x_0_0, 0))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.blocks_multiply_const_vxx_1_0, 0))
        self.connect((self.blocks_multiply_const_vxx_1_0, 0), (self.qtgui_number_sink_0_0, 0))
        self.connect((self.blocks_short_to_float_0, 0), (self.blocks_multiply_const_vxx_1, 0))
        self.connect((self.blocks_stream_to_vector_0_0, 0), (self.fft_vxx_0_0, 0))
        self.connect((self.fft_vxx_0_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_multiply_conjugate_cc_0, 1))


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
        self.set_df(self.samp_rate/self.k_bins)
        self.set_distance_per_sample(self.c/self.samp_rate/2)
        self.set_max_freq(self.samp_rate*0.4)
        self.qtgui_freq_sink_x_0_0.set_frequency_range(0, self.samp_rate)
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_max_freq(self):
        return self.max_freq

    def set_max_freq(self, max_freq):
        self.max_freq = max_freq
        self.set_alpha((self.max_freq-self.min_freq)/self.t_chirp)
        self.set_min_freq(-self.max_freq)

    def get_t_chirp(self):
        return self.t_chirp

    def set_t_chirp(self, t_chirp):
        self.t_chirp = t_chirp
        self.set_alpha((self.max_freq-self.min_freq)/self.t_chirp)

    def get_min_freq(self):
        return self.min_freq

    def set_min_freq(self, min_freq):
        self.min_freq = min_freq
        self.set_alpha((self.max_freq-self.min_freq)/self.t_chirp)

    def get_k_bins(self):
        return self.k_bins

    def set_k_bins(self, k_bins):
        self.k_bins = k_bins
        self.set_df(self.samp_rate/self.k_bins)

    def get_c(self):
        return self.c

    def set_c(self, c):
        self.c = c
        self.set_distance_per_sample(self.c/self.samp_rate/2)
        self.blocks_multiply_const_vxx_1_0.set_k((self.c/2/self.alpha))

    def get_radio_tx_gain(self):
        return self.radio_tx_gain

    def set_radio_tx_gain(self, radio_tx_gain):
        self.radio_tx_gain = radio_tx_gain
        self.uhd_usrp_sink_0.set_gain(self.radio_tx_gain, 0)

    def get_radio_rx_gain(self):
        return self.radio_rx_gain

    def set_radio_rx_gain(self, radio_rx_gain):
        self.radio_rx_gain = radio_rx_gain
        self.uhd_usrp_source_0.set_gain(self.radio_rx_gain, 0)

    def get_radio_center(self):
        return self.radio_center

    def set_radio_center(self, radio_center):
        self.radio_center = radio_center
        self.uhd_usrp_sink_0.set_center_freq(self.radio_center, 0)
        self.uhd_usrp_source_0.set_center_freq(self.radio_center, 0)

    def get_min_buffer(self):
        return self.min_buffer

    def set_min_buffer(self, min_buffer):
        self.min_buffer = min_buffer

    def get_max_buffer(self):
        return self.max_buffer

    def set_max_buffer(self, max_buffer):
        self.max_buffer = max_buffer

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
        self.blocks_multiply_const_vxx_1.set_k((1*self.df))

    def get_calibration_delay(self):
        return self.calibration_delay

    def set_calibration_delay(self, calibration_delay):
        self.calibration_delay = calibration_delay
        self.blocks_delay_0.set_dly(int(self.calibration_delay))

    def get_alpha(self):
        return self.alpha

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.blocks_multiply_const_vxx_1_0.set_k((self.c/2/self.alpha))




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
