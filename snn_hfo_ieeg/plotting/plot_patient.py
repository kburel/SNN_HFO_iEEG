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


def _convert_to_labels_to_hfo_rate_dict(intervals):
    label_to_hfo_rates = {}
    for channels in intervals.values():
        for channel in channels:
            _append_or_create(
                dict=label_to_hfo_rates,
                key=channel.metadata.channel_label,
                value=channel.hfo_detection.result.frequency * 60)

    return label_to_hfo_rates


def _plot_bar(axes, intervals):
    label_to_hfo_rates = _convert_to_labels_to_hfo_rate_dict(intervals)

    labels = list(label_to_hfo_rates.keys())
    hfo_rates = label_to_hfo_rates.values()

    mean_hfo_rates = [mean(_) for _ in hfo_rates]
    standard_deviations = [np.std(_) for _ in hfo_rates] \
        if len(intervals) > 1 else None
    axes.bar(
        x=labels,
        height=mean_hfo_rates,
        width=0.3,
        edgecolor='k',
        ecolor='#0218f5',
        alpha=0.9, color='#2f70b6',
        yerr=standard_deviations,
        capsize=2)


def plot_mean_hfo_rate(intervals: Intervals):
    if len(intervals) == 0:
        return

    fig, axes = plt.subplots(figsize=(15, 5))
    plt.rc('font', family='sans-serif')
    plt.tight_layout()
    fig.subplots_adjust(bottom=0.15, wspace=0.2, hspace=0.2)

    _plot_bar(axes, intervals)

    labels = axes.get_xticklabels()
    for label in labels:
        label.set_rotation(45)
        label.set_horizontalalignment('right')
        label.set_size = 16

    axes.set_xlabel('Electrode label', fontsize=18)
    axes.set_ylabel('HFO rate (event/min)', fontsize=18)

    axes.tick_params(axis='y', labelsize=16, length=8)
    axes.tick_params(axis='x', labelsize=16, length=8)

    axes.spines['top'].set_visible(False)
    axes.spines['right'].set_visible(False)
