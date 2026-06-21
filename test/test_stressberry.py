import pytest

import stressberry.main as main


def test_stress_cpu_invokes_external_stress_with_timeout(monkeypatch):
    calls = []

    def fake_check_call(command):
        calls.append(command)

    monkeypatch.setattr(main.subprocess, "check_call", fake_check_call)

    main.stress_cpu(num_cpus=2, time=7)

    assert calls == [["stress", "--cpu", "2", "--timeout", "7s"]]


def test_stress_cpu_reports_missing_stress_command(monkeypatch):
    def fake_check_call(command):
        raise FileNotFoundError("stress")

    monkeypatch.setattr(main.subprocess, "check_call", fake_check_call)

    with pytest.raises(RuntimeError, match="Install the stress package"):
        main.stress_cpu(num_cpus=2, time=7)


def test_stress_cpu_reports_failing_stress_command(monkeypatch):
    def fake_check_call(command):
        raise main.subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(main.subprocess, "check_call", fake_check_call)

    with pytest.raises(RuntimeError, match="stress command failed"):
        main.stress_cpu(num_cpus=2, time=7)


def test_measure_temp_reads_millidegrees_from_file(tmp_path):
    temperature_file = tmp_path / "temp"
    temperature_file.write_text("42345")

    assert main.measure_temp(filename=temperature_file) == pytest.approx(42.345)


def test_measure_temp_reports_malformed_file_contents(tmp_path):
    temperature_file = tmp_path / "temp"
    temperature_file.write_text("not-a-number")

    with pytest.raises(RuntimeError, match="Invalid temperature value"):
        main.measure_temp(filename=temperature_file)


def test_measure_temp_reads_vcgencmd_output(monkeypatch):
    monkeypatch.setattr(
        main.subprocess,
        "check_output",
        lambda command: b"temp=48.2'C\n",
    )

    assert main.measure_temp() == pytest.approx(48.2)


def test_measure_temp_reports_missing_vcgencmd(monkeypatch):
    def fake_check_output(command):
        raise FileNotFoundError("vcgencmd")

    monkeypatch.setattr(main.subprocess, "check_output", fake_check_output)

    with pytest.raises(RuntimeError, match="vcgencmd is not available"):
        main.measure_temp()


def test_measure_temp_reports_malformed_vcgencmd_output(monkeypatch):
    monkeypatch.setattr(
        main.subprocess,
        "check_output",
        lambda command: b"temperature unavailable\n",
    )

    with pytest.raises(RuntimeError, match="Unexpected vcgencmd temperature"):
        main.measure_temp()


def test_measure_core_frequency_reads_khz_from_file(tmp_path):
    frequency_file = tmp_path / "scaling_cur_freq"
    frequency_file.write_text("1500000")

    assert main.measure_core_frequency(filename=frequency_file) == 1500


def test_measure_core_frequency_reports_malformed_file_contents(tmp_path):
    frequency_file = tmp_path / "scaling_cur_freq"
    frequency_file.write_text("unknown")

    with pytest.raises(RuntimeError, match="Invalid CPU frequency value"):
        main.measure_core_frequency(filename=frequency_file)


def test_measure_core_frequency_reads_vcgencmd_output(monkeypatch):
    monkeypatch.setattr(
        main.subprocess,
        "check_output",
        lambda command: b"frequency(48)=1400000000\n",
    )

    assert main.measure_core_frequency() == 1400


def test_measure_core_frequency_reports_malformed_vcgencmd_output(monkeypatch):
    monkeypatch.setattr(
        main.subprocess,
        "check_output",
        lambda command: b"clock unknown\n",
    )

    with pytest.raises(RuntimeError, match="Unexpected vcgencmd frequency"):
        main.measure_core_frequency()


def test_measure_core_frequency_reports_failing_vcgencmd(monkeypatch):
    def fake_check_output(command):
        raise main.subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(main.subprocess, "check_output", fake_check_output)

    with pytest.raises(RuntimeError, match="vcgencmd command failed"):
        main.measure_core_frequency()


def test_measure_ambient_temperature_reports_missing_dependency(monkeypatch):
    real_import = __builtins__["__import__"]

    def fake_import(name, *args, **kwargs):
        if name == "Adafruit_DHT":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setitem(__builtins__, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="Install the optional Adafruit_DHT"):
        main.measure_ambient_temperature()


def test_measure_ambient_temperature_reports_invalid_sensor(monkeypatch):
    class FakeAdafruitDHT:
        DHT11 = object()
        DHT22 = object()
        AM2302 = object()

        @staticmethod
        def read_retry(sensor, pin):
            return None, 21.0

    real_import = __builtins__["__import__"]

    def fake_import(name, *args, **kwargs):
        if name == "Adafruit_DHT":
            return FakeAdafruitDHT
        return real_import(name, *args, **kwargs)

    monkeypatch.setitem(__builtins__, "__import__", fake_import)

    with pytest.raises(
        RuntimeError, match="Invalid ambient temperature sensor"
    ):
        main.measure_ambient_temperature(sensor_type="99")


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
