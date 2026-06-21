import re
import subprocess
import time as tme
from os import cpu_count
from pathlib import Path


def stress_cpu(num_cpus, time):
    command = ["stress", "--cpu", str(num_cpus), "--timeout", f"{time}s"]
    try:
        subprocess.check_call(command)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "The 'stress' command is not available. "
            "Install the stress package, then try again."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"stress command failed with exit status {exc.returncode}."
        ) from exc
    return


def cooldown(interval=60, filename=None):
    """Lets the CPU cool down until the temperature does not change anymore."""
    prev_tmp = measure_temp(filename=filename)
    while True:
        tme.sleep(interval)
        tmp = measure_temp(filename=filename)
        print(
            f"Current temperature: {tmp:4.1f}°C - "
            f"Previous temperature: {prev_tmp:4.1f}°C"
        )
        if abs(tmp - prev_tmp) < 0.2:
            break
        prev_tmp = tmp
    return tmp


def _read_float_from_file(filename, *, value_name):
    try:
        return float(Path(filename).read_text())
    except OSError as exc:
        raise RuntimeError(
            f"Could not read {value_name} file {filename!s}."
        ) from exc
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid {value_name} value in {filename!s}; expected a number."
        ) from exc


def _run_vcgencmd(command, *, value_name):
    try:
        return subprocess.check_output(command).decode("utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(
            "vcgencmd is not available. Run on a Raspberry Pi with "
            "raspberrypi-utils installed, or pass a file path option."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"vcgencmd command failed while reading {value_name} "
            f"with exit status {exc.returncode}."
        ) from exc
    except UnicodeDecodeError as exc:
        raise RuntimeError(
            f"Unexpected vcgencmd {value_name} output; could not decode it."
        ) from exc


def measure_temp(filename=None):
    """Returns the core temperature in Celsius."""
    if filename is not None:
        return _read_float_from_file(filename, value_name="temperature") / 1000

    # Using vcgencmd is specific to the raspberry pi
    out = _run_vcgencmd(["vcgencmd", "measure_temp"], value_name="temperature")
    match = re.fullmatch(r"temp=([+-]?\d+(?:\.\d+)?)'C\s*", out)
    if match is None:
        raise RuntimeError(
            "Unexpected vcgencmd temperature output; expected "
            "format like temp=48.2'C."
        )
    return float(match.group(1))


def measure_core_frequency(filename=None):
    """Returns the CPU frequency in MHz"""
    if filename is not None:
        return (
            _read_float_from_file(filename, value_name="CPU frequency") / 1000
        )

    # Only vcgencmd measure_clock arm is accurate on Raspberry Pi.
    # Per: https://www.raspberrypi.org/forums/viewtopic.php?f=63&t=219358&start=25
    out = _run_vcgencmd(
        ["vcgencmd", "measure_clock", "arm"], value_name="frequency"
    )
    match = re.fullmatch(r"frequency\(\d+\)=([0-9]+)\s*", out)
    if match is None:
        raise RuntimeError(
            "Unexpected vcgencmd frequency output; expected "
            "format like frequency(48)=1400000000."
        )
    return float(match.group(1)) / 1000000


def measure_ambient_temperature(sensor_type="2302", pin="23"):
    """Uses Adafruit temperature sensor to measure ambient temperature"""
    try:
        import Adafruit_DHT  # Late import so that library is only needed if requested
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional Adafruit_DHT dependency to use ambient "
            "temperature measurements: pip install Adafruit_DHT."
        ) from exc

    sensor_map = {
        "11": Adafruit_DHT.DHT11,
        "22": Adafruit_DHT.DHT22,
        "2302": Adafruit_DHT.AM2302,
    }
    try:
        sensor = sensor_map[sensor_type]
    except KeyError as exc:
        raise RuntimeError(
            "Invalid ambient temperature sensor. Choose one of: 11, 22, 2302."
        ) from exc
    _, temperature = Adafruit_DHT.read_retry(sensor, pin)
    # Note that sometimes you won't get a reading and the results will be null (because
    # Linux can't guarantee the timing of calls to read the sensor).  The read_retry
    # call will attempt to read the sensor 15 times with a 2 second delay.  Care should
    # be taken when reading if on a time sensitive path Temperature is in °C but can
    # also be None
    return temperature


def test(stress_duration, idle_duration, cores):
    """Run stress test for specified duration with specified idle times
    at the start and end of the test.
    """
    if cores is None:
        cores = cpu_count()

    print(
        f"Preparing to stress [{cores}] CPU Cores for [{stress_duration}] seconds"
    )
    print(f"Idling for {idle_duration} seconds...")
    tme.sleep(idle_duration)

    stress_cpu(num_cpus=cores, time=stress_duration)

    print(f"Idling for {idle_duration} seconds...")
    tme.sleep(idle_duration)
