import argparse
from collections.abc import Sized

import yaml

from .helpers import _get_version_text


def plot(argv=None):
    import matplotx
    import matplotlib.pyplot as plt

    plt.style.use(matplotx.styles.dufte)

    parser = _get_parser_plot()
    args = parser.parse_args(argv)

    data = [yaml.load(f, Loader=yaml.SafeLoader) for f in args.infiles]

    try:
        fig = plt.figure()
        ax1 = fig.add_subplot(1, 1, 1)
        for d in data:
            time_data = _required_series(d, "time")
            temperature_data = _required_series(d, "temperature")
            _require_same_length(
                "temperature", temperature_data, "time", time_data
            )
            if args.delta_t:
                ambient_data = _ambient_series(d)
                _require_same_length(
                    "ambient", ambient_data, "temperature", temperature_data
                )
                temperature_data = [
                    temperature - ambient
                    for temperature, ambient in zip(
                        temperature_data, ambient_data, strict=True
                    )
                ]

            plt.plot(time_data, temperature_data, label=d["name"])
    except PlotDataError as exc:
        parser.exit(1, f"error: {exc}\n")

    matplotx.line_labels()

    if args.delta_t:
        plot_yaxis_label = "Δ temperature [°C over ambient]"
    else:
        plot_yaxis_label = "temperature [°C]"
    plt.xlabel("time [s]")
    plt.ylabel(plot_yaxis_label)

    if args.temp_lims:
        ax1.set_ylim(*args.temp_lims)

    # Only plot frequencies when using a single input file
    if len(data) == 1 and args.frequency:
        d = data[0]
        if "cpu frequency" not in d:
            print("Source data does not contain CPU frequency data.")
        else:
            try:
                frequency_data = _required_series(d, "cpu frequency")
                time_data = _required_series(d, "time")
                _require_same_length(
                    "cpu frequency", frequency_data, "time", time_data
                )
            except PlotDataError as exc:
                parser.exit(1, f"error: {exc}\n")
            ax2 = plt.twinx()
            ax2.set_ylabel("core frequency (MHz)")
            if args.freq_lims:
                ax2.set_ylim(*args.freq_lims)
            ax2.plot(
                time_data,
                frequency_data,
                label=d["name"],
                color="C1",
                alpha=0.9,
            )
            # Put ax1 plot in front of ax2 and hide the canvas.
            ax1.set_zorder(ax2.get_zorder() + 1)
            ax1.patch.set_visible(False)

    if args.outfile is not None:
        plt.savefig(
            args.outfile,
            transparent=args.transparent,
            bbox_inches="tight",
            dpi=args.dpi,
        )
    else:
        plt.show()
    return


class PlotDataError(ValueError):
    pass


def _required_series(data, key):
    try:
        series = data[key]
    except KeyError as exc:
        raise PlotDataError(f"source data is missing {key!r}") from exc
    if not isinstance(series, Sized):
        raise PlotDataError(f"{key} must be a sequence")
    return series


def _ambient_series(data):
    if "ambient" not in data:
        raise PlotDataError("delta-T plotting requires ambient data")
    return _required_series(data, "ambient")


def _require_same_length(left_name, left, right_name, right):
    if len(left) != len(right):
        raise PlotDataError(
            f"{left_name} contains {len(left)} samples but "
            f"{right_name} contains {len(right)}"
        )


def _get_parser_plot():
    parser = argparse.ArgumentParser(description="Plot stress test data.")
    parser.add_argument(
        "--version", "-v", action="version", version=_get_version_text()
    )
    parser.add_argument(
        "infiles",
        nargs="+",
        type=argparse.FileType("r"),
        help="input YAML file(s) (default: stdin)",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        help=(
            "if specified, the plot is written to this file "
            "(default: show on screen)"
        ),
    )
    parser.add_argument(
        "-t",
        "--temp-lims",
        type=float,
        nargs=2,
        default=None,
        help="limits for the temperature (default: data limits)",
    )
    parser.add_argument(
        "-d",
        "--dpi",
        type=int,
        default=None,
        help="image resolution in dots per inch when written to file",
    )
    parser.add_argument(
        "-f",
        "--frequency",
        help="plot CPU core frequency (single input files only)",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--freq-lims",
        type=float,
        nargs=2,
        default=None,
        help="limits for the frequency scale (default: data limits)",
    )
    parser.add_argument(
        "--not-transparent",
        dest="transparent",
        help="do not make images transparent",
        action="store_false",
        default=True,
    )
    parser.add_argument(
        "--delta-t",
        action="store_true",
        default=False,
        help="Use Delta-T (core - ambient) temperature instead of CPU core temperature",
    )
    return parser
