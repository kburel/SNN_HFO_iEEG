from functools import reduce
import warnings
from brian2 import Network, run, SpikeGeneratorGroup, SpikeMonitor, store, restore
from brian2.units import us, amp, second
from teili.core.groups import Neurons, Connections
from teili.models.builder.neuron_equation_builder import NeuronEquationBuilder
from teili.models.builder.synapse_equation_builder import SynapseEquationBuilder
from snn_hfo_ieeg.functions.signal_to_spike import concatenate_spikes
from snn_hfo_ieeg.functions.dynapse_biases import get_current
from snn_hfo_ieeg.stages.snn.tau_generation import generate_concatenated_taus
from snn_hfo_ieeg.stages.snn.weight_generation import generate_weights
from snn_hfo_ieeg.stages.snn.model_paths import load_model_paths
from snn_hfo_ieeg.stages.snn.concatenation import NeuronCount
from snn_hfo_ieeg.stages.shared_config import MeasurementMode


def _append_spikes(spikes, spike_train):
    spikes.append(spike_train.up)
    spikes.append(spike_train.down)
    return spikes


def _concatenate_filtered_spikes(filtered_spikes):
    spikes = reduce(_append_spikes, filtered_spikes, [])
    return concatenate_spikes(spikes)


def _measurement_mode_to_input_count(measurement_mode):
    if measurement_mode is MeasurementMode.IEEG:
        return 4
    if measurement_mode is MeasurementMode.ECOG:
        return 2
    if measurement_mode is MeasurementMode.SCALP:
        return 2
    raise ValueError(
        f'measurement_mode is outside valid range. Allowed values: {MeasurementMode}, instead got: {measurement_mode}')


def _read_neuron_counts(configuration):
    input_count = _measurement_mode_to_input_count(
        configuration.measurement_mode)
    return NeuronCount(input_count, configuration.hidden_neuron_count)


def _create_input_layer(filtered_spikes, input_count):
    input_spiketimes, input_neurons_id = _concatenate_filtered_spikes(
        filtered_spikes)
    return SpikeGeneratorGroup(input_count,
                               input_neurons_id,
                               input_spiketimes*second,
                               dt=100*us, name='input')


def _create_hidden_layer(model_paths, hidden_neuron_count):
    equation_builder = NeuronEquationBuilder.import_eq(
        model_paths.neuron, num_inputs=1)
    hidden_layer = Neurons(
        hidden_neuron_count, equation_builder=equation_builder, name='hidden_layer', dt=100*us)
    return hidden_layer


def _create_synapses(input_layer, hidden_layer, model_paths, neuron_counts):
    equation_builder = SynapseEquationBuilder.import_eq(model_paths.synapse)
    synapses = Connections(
        input_layer, hidden_layer, equation_builder=equation_builder, name='synapses', verbose=False, dt=100*us)

    synapses.connect()

    synapses.weight = generate_weights(neuron_counts)
    taus = generate_concatenated_taus(neuron_counts)
    synapses.I_tau = get_current(taus*1e-3) * amp

    return synapses


def snn_stage(filtered_spikes, duration, configuration, cache):
    warnings.simplefilter("ignore", DeprecationWarning)
    if len(cache) == 0:
        cache['model_paths'] = load_model_paths()
        cache['neuron_counts'] = _read_neuron_counts(configuration)
        cache['hidden_layer'] = _create_hidden_layer(
            cache['model_paths'], cache['neuron_counts'].hidden)
        cache['spike_monitor_hidden'] = SpikeMonitor(cache['hidden_layer'])
        cache['network'] = Network(
            cache['hidden_layer'], cache['spike_monitor_hidden'])
        cache['network'].store()

    network = cache['network']
    network.restore()
    input_layer = _create_input_layer(
        filtered_spikes, cache['neuron_counts'].input)
    network.add(input_layer)
    synapses = _create_synapses(
        input_layer,
        cache['hidden_layer'],
        cache['model_paths'],
        cache['neuron_counts'])

    network.add(synapses)
    network.run(duration * second)
    network.remove(input_layer)
    network.remove(synapses)

    return cache['spike_monitor_hidden']
