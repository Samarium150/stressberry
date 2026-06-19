import pytest

import stressberry.main as main


def test_stress_cpu_invokes_external_stress_with_timeout(monkeypatch):
    calls = []

    def fake_check_call(command):
        calls.append(command)

    monkeypatch.setattr(main.subprocess, "check_call", fake_check_call)

    main.stress_cpu(num_cpus=2, time=7)

    assert calls == [["stress", "--cpu", "2", "--timeout", "7s"]]


def test_measure_temp_reads_millidegrees_from_file(tmp_path):
    temperature_file = tmp_path / "temp"
    temperature_file.write_text("42345")

    assert main.measure_temp(filename=temperature_file) == pytest.approx(42.345)


def test_measure_temp_reads_vcgencmd_output(monkeypatch):
    monkeypatch.setattr(
        main.subprocess,
        "check_output",
        lambda command: b"temp=48.2'C\n",
    )

    assert main.measure_temp() == pytest.approx(48.2)


def test_measure_core_frequency_reads_khz_from_file(tmp_path):
    frequency_file = tmp_path / "scaling_cur_freq"
    frequency_file.write_text("1500000")

    assert main.measure_core_frequency(filename=frequency_file) == 1500


def test_measure_core_frequency_reads_vcgencmd_output(monkeypatch):
    monkeypatch.setattr(
        main.subprocess,
        "check_output",
        lambda command: b"frequency(48)=1400000000\n",
    )

    assert main.measure_core_frequency() == 1400


def test_cooldown_stops_after_temperature_stabilizes(monkeypatch, capsys):
    temperatures = iter([55.0, 50.0, 49.9])
    sleep_intervals = []

    monkeypatch.setattr(
        main,
        "measure_temp",
        lambda filename=None: next(temperatures),
    )
    monkeypatch.setattr(
        main.tme,
        "sleep",
        lambda interval: sleep_intervals.append(interval),
    )

    final_temperature = main.cooldown(interval=3, filename="sensor")

    assert final_temperature == pytest.approx(49.9)
    assert sleep_intervals == [3, 3]
    assert "Current temperature: 49.9" in capsys.readouterr().out


def test_test_uses_configured_durations_and_cpu_count(monkeypatch):
    sleep_intervals = []
    stress_calls = []

    monkeypatch.setattr(main, "cpu_count", lambda: 4)
    monkeypatch.setattr(
        main.tme,
        "sleep",
        lambda interval: sleep_intervals.append(interval),
    )
    monkeypatch.setattr(
        main,
        "stress_cpu",
        lambda num_cpus, time: stress_calls.append((num_cpus, time)),
    )

    main.test(stress_duration=9, idle_duration=2, cores=None)

    assert sleep_intervals == [2, 2]
    assert stress_calls == [(4, 9)]
