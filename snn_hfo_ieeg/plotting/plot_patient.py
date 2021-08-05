from typing import List, TypedDict, NamedTuple
from statistics import mean
import numpy as np
import matplotlib.pyplot as plt
from snn_hfo_ieeg.user_facing_data import HfoDetectionWithAnalytics, Metadata


class ChannelData(NamedTuple):
    metadata: Metadata
    hfo_detection: HfoDetectionWithAnalytics


class Intervals(TypedDict):
    index: int
    channel_data: List[ChannelData]


class PatientDebugError(Exception):
    def __init__(self, message, intervals: Intervals):
        super().__init__(message)
        self.intervals = intervals


def plot_internal_patient_debug(intervals: Intervals):
    raise PatientDebugError(
        "plot_internal_patient_debug is just here for debugging purposes and should not be called",
        intervals)


def _append_or_create(dict, key, value):
    if key not in dict:
        dict[key] = [value]
    else:
        dict[key].append(value)


def plot_mean_hfo_rate(intervals: Intervals):
    if len(intervals) == 0:
        return

    label_to_hfo_rates = {}
    for channels in intervals.values():
        for channel in channels:
            _append_or_create(
                dict=label_to_hfo_rates,
                key=channel.metadata.channel_label,
                value=channel.hfo_detection.result.frequency * 60)

    labels = list(label_to_hfo_rates.keys())
    hfo_rates = label_to_hfo_rates.values()
    mean_hfo_rates = [mean(_) for _ in hfo_rates]
    standard_deviations = [np.std(_) for _ in hfo_rates] \
        if len(intervals) > 1 else None

    figure_size = (15, 5)
    fig, axes = plt.subplots(figsize=figure_size)
    plt.rc('font', family='sans-serif')
    plt.tight_layout()
    fig.subplots_adjust(wspace=0.2, hspace=0.2)

    axes.bar(
        x=labels,
        height=mean_hfo_rates,
        edgecolor='k',
        ecolor='#0218f5',
        alpha=0.9, color='#2f70b6',
        yerr=standard_deviations,
        capsize=2)

    axes.set_xticklabels(labels, rotation=45,
                         fontsize=16, horizontalalignment='right')

    axes.set_xlabel('Electrode label', fontsize=18)
    axes.set_ylabel('HFO rate (event/min)', fontsize=18)

    axes.tick_params(axis='y', labelsize=16, length=8)
    axes.tick_params(axis='x', labelsize=16, length=8)

    axes.spines['top'].set_visible(False)
    axes.spines['right'].set_visible(False)
