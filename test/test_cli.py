import os
from importlib import import_module

import matplotlib
import pytest
import yaml

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import matplotx

plot_module = import_module("stressberry.cli.plot")
run_module = import_module("stressberry.cli.run")


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


class SamplingThread:
    def __init__(self, target, args=()):
        self._target = target
        self._remaining_samples = 0

    def start(self):
        self._target()
        self._remaining_samples = 3

    def is_alive(self):
        return self._remaining_samples > 0

    def join(self, timeout=None):
        self._remaining_samples -= 1


def write_run_data(path, *, include_frequency=True):
    data = {
        "name": "dataset",
        "time": [0, 1, 2],
        "temperature": [40.0, 44.0, 46.5],
        "ambient": [20.0, 21.0, 21.5],
    }
    if include_frequency:
        data["cpu frequency"] = [900.0, 1200.0, 1500.0]
    path.write_text(yaml.safe_dump(data))
    return data


def test_run_parser_accepts_sensor_and_timing_options(tmp_path):
    output_file = tmp_path / "out.yml"

    args = run_module._get_parser_run().parse_args(
        [
            "--name",
            "bench",
            "--temperature-file",
            "temp",
            "--duration",
            "12",
            "--idle",
            "4",
            "--cooldown",
            "1",
            "--cores",
            "2",
            "--frequency-file",
            "freq",
            "--ambient",
            "22",
            "26",
            str(output_file),
        ]
    )

    assert args.name == "bench"
    assert args.temperature_file == "temp"
    assert args.duration == 12
    assert args.idle == 4
    assert args.cooldown == 1
    assert args.cores == 2
    assert args.frequency_file == "freq"
    assert args.ambient == ["22", "26"]
    assert args.outfile.name == str(output_file)


def test_run_writes_yaml_with_normalized_times_and_ambient_fallback(
    monkeypatch, tmp_path, capsys
):
    output_file = tmp_path / "stressberry.yml"
    temperatures = iter([50.0, 51.0, 52.0])
    frequencies = iter([1400.0, 1350.0, 1200.0])
    ambient_temperatures = iter([21.0, None, 22.0])
    times = iter([100.0, 102.0, 104.5])
    test_calls = []

    monkeypatch.setattr(run_module, "cooldown", lambda **kwargs: 45.0)
    monkeypatch.setattr(
        run_module,
        "test",
        lambda duration, idle, cores: test_calls.append(
            (duration, idle, cores)
        ),
    )
    monkeypatch.setattr(run_module.threading, "Thread", SamplingThread)
    monkeypatch.setattr(run_module.time, "time", lambda: next(times))
    monkeypatch.setattr(
        run_module,
        "measure_temp",
        lambda filename=None: next(temperatures),
    )
    monkeypatch.setattr(
        run_module,
        "measure_core_frequency",
        lambda filename=None: next(frequencies),
    )
    monkeypatch.setattr(
        run_module,
        "measure_ambient_temperature",
        lambda sensor_type, pin: next(ambient_temperatures),
    )

    run_module.run(
        [
            "--name",
            "bench",
            "--temperature-file",
            "temp",
            "--frequency-file",
            "freq",
            "--duration",
            "9",
            "--idle",
            "2",
            "--cooldown",
            "1",
            "--cores",
            "4",
            "--ambient",
            "2302",
            "23",
            str(output_file),
        ]
    )

    yaml_lines = [
        line
        for line in output_file.read_text().splitlines()
        if not line.startswith("#")
    ]
    data = yaml.safe_load("\n".join(yaml_lines))

    assert test_calls == [(9, 2, 4)]
    assert data == {
        "name": "bench",
        "time": [0.0, 2.0, 4.5],
        "temperature": [50.0, 51.0, 52.0],
        "cpu frequency": [1400.0, 1350.0, 1200.0],
        "ambient": [21.0, 21.0, 22.0],
    }
    assert "using last good value" in capsys.readouterr().out


def test_run_uses_zero_when_first_ambient_reading_is_missing(
    monkeypatch, tmp_path, capsys
):
    output_file = tmp_path / "stressberry.yml"
    times = iter([1.0, 2.0, 3.0])
    temperatures = iter([50.0, 51.0, 52.0])
    frequencies = iter([1400.0, 1350.0, 1200.0])
    ambient_temperatures = iter([None, 22.0, 23.0])

    monkeypatch.setattr(run_module, "cooldown", lambda **kwargs: 45.0)
    monkeypatch.setattr(run_module, "test", lambda duration, idle, cores: None)
    monkeypatch.setattr(run_module.threading, "Thread", SamplingThread)
    monkeypatch.setattr(run_module.time, "time", lambda: next(times))
    monkeypatch.setattr(
        run_module,
        "measure_temp",
        lambda filename=None: next(temperatures),
    )
    monkeypatch.setattr(
        run_module,
        "measure_core_frequency",
        lambda filename=None: next(frequencies),
    )
    monkeypatch.setattr(
        run_module,
        "measure_ambient_temperature",
        lambda sensor_type, pin: next(ambient_temperatures),
    )

    run_module.run(["--ambient", "2302", "23", str(output_file)])

    yaml_lines = [
        line
        for line in output_file.read_text().splitlines()
        if not line.startswith("#")
    ]
    data = yaml.safe_load("\n".join(yaml_lines))

    assert data["ambient"] == [0, 22.0, 23.0]
    assert (
        "Could not read ambient temperature sensor 2302 on pin 23"
        in capsys.readouterr().out
    )


def test_plot_parser_accepts_save_and_axis_options(tmp_path):
    input_file = tmp_path / "input.yml"
    output_file = tmp_path / "plot.png"
    write_run_data(input_file)

    args = plot_module._get_parser_plot().parse_args(
        [
            str(input_file),
            "--outfile",
            str(output_file),
            "--temp-lims",
            "20",
            "90",
            "--frequency",
            "--freq-lims",
            "500",
            "2000",
            "--not-transparent",
            "--delta-t",
        ]
    )

    assert args.infiles[0].name == str(input_file)
    assert args.outfile == str(output_file)
    assert args.temp_lims == [20.0, 90.0]
    assert args.frequency is True
    assert args.freq_lims == [500.0, 2000.0]
    assert args.transparent is False
    assert args.delta_t is True


def test_plot_delta_t_saves_file_without_gui(monkeypatch, tmp_path):
    input_file = tmp_path / "input.yml"
    output_file = tmp_path / "plot.png"
    write_run_data(input_file)
    plotted = []
    saved = []

    monkeypatch.setattr(matplotx, "line_labels", lambda: None)
    monkeypatch.setattr(
        plt,
        "plot",
        lambda x, y, label: plotted.append((x, y, label)),
    )
    monkeypatch.setattr(
        plt,
        "savefig",
        lambda outfile, **kwargs: saved.append((outfile, kwargs)),
    )

    plot_module.plot([str(input_file), "--delta-t", "-o", str(output_file)])

    assert plotted == [([0, 1, 2], [20.0, 23.0, 25.0], "dataset")]
    assert saved[0][0] == str(output_file)
    assert saved[0][1]["transparent"] is True


def test_plot_show_branch_without_gui(monkeypatch, tmp_path):
    input_file = tmp_path / "input.yml"
    write_run_data(input_file)
    shown = []

    monkeypatch.setattr(matplotx, "line_labels", lambda: None)
    monkeypatch.setattr(plt, "show", lambda: shown.append(True))

    plot_module.plot([str(input_file)])

    assert shown == [True]


def test_plot_frequency_adds_secondary_axis(monkeypatch, tmp_path):
    input_file = tmp_path / "input.yml"
    write_run_data(input_file)

    monkeypatch.setattr(matplotx, "line_labels", lambda: None)
    monkeypatch.setattr(plt, "show", lambda: None)

    plot_module.plot([str(input_file), "--frequency"])

    assert len(plt.gcf().axes) == 2


def test_plot_warns_when_frequency_data_is_missing(
    monkeypatch, tmp_path, capsys
):
    input_file = tmp_path / "input.yml"
    write_run_data(input_file, include_frequency=False)

    monkeypatch.setattr(matplotx, "line_labels", lambda: None)
    monkeypatch.setattr(plt, "show", lambda: None)

    plot_module.plot([str(input_file), "--frequency"])

    assert (
        "Source data does not contain CPU frequency data."
        in capsys.readouterr().out
    )
    assert len(plt.gcf().axes) == 1


@pytest.mark.skipif(
    os.environ.get("STRESSBERRY_RUN_SYSTEM_TESTS") != "1",
    reason="requires Raspberry Pi tools and real stress binary",
)
def test_optional_system_stress_path():
    import stressberry

    stressberry.stress_cpu(1, 1)
