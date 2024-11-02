import base64
import io
import os

import pandas as pd
from fasthtml import common as fh
from matplotlib import pyplot as plt


def save_data(data, name, ext):
    os.makedirs(f"saved/{ext}", exist_ok=True)
    if ext in ["png", "jpg", "jpeg"]:
        data.savefig(f"saved/{ext}/{name}.{ext}", format=ext)
    elif ext == "csv":
        data.to_csv(f"saved/{ext}/{name}.{ext}", index=False)


def get_items_from_request(response: fh.FormData, *args) -> dict[str, str]:
    values = {}
    for key_name in args:
        values[key_name] = response.get(key_name)

    return values


def get_correlation_df(df: pd.DataFrame):
    column_names = list(df.columns)
    corr_dict = {
        "col1": [],
        "col2": [],
        "pearson": [],
        "kendall": [],
        "spearman": [],
    }

    for i, col_name in enumerate(column_names):
        while i >= 0:
            corr_dict["col1"].append(col_name)
            corr_dict["col2"].append(column_names[i])
            try:
                corr_dict["pearson"].append(
                    df[col_name].corr(df[column_names[i]], method="pearson")
                )
            except ValueError:
                corr_dict["pearson"].append("")

            try:
                corr_dict["kendall"].append(
                    df[col_name].corr(df[column_names[i]], method="kendall")
                )
            except ValueError:
                corr_dict["kendall"].append("")

            try:
                corr_dict["spearman"].append(
                    df[col_name].corr(df[column_names[i]], method="spearman")
                )
            except ValueError:
                corr_dict["spearman"].append("")

            i -= 1

    corr_df = pd.DataFrame(corr_dict)
    corr_df = corr_df[corr_df["pearson"] != ""]
    corr_df = corr_df[corr_df["col1"] != corr_df["col2"]]

    corr_df = corr_df.assign(
        max=corr_df[["pearson", "kendall", "spearman"]].abs().max(axis=1)
    )
    corr_df = corr_df.sort_values("max", ascending=False).drop("max", axis=1)
    corr_df = corr_df.reset_index(drop=True)

    return corr_df


def get_plot_selectors(headers: list[str]):
    correlation_button = fh.Button(
        "Get Correlation",
        hx_post="/get-correlation",
        hx_target="#output-div",
        hx_swap="innerHTML",
        id="correlation-button",
    )

    column_selector_1 = fh.Select(
        "Select column",
        *[fh.Option(column_name, value=column_name) for column_name in headers],
        id="column-selector-1",
    )

    column_selector_2 = fh.Select(
        "Select column",
        *[fh.Option(column_name, value=column_name) for column_name in headers],
        id="column-selector-2",
    )

    plot_types = ["line", "scatter", "hist", "bar-sum", "bar-count"]
    plot_type_selector = fh.Select(
        "Select plot type",
        *[fh.Option(plot_type, value=plot_type) for plot_type in plot_types],
        id="plot-type-selector",
    )

    title_text = fh.P("Title")
    title_input = fh.Input(type="text", id="title-input")

    x_axis_text = fh.P("X Axis Title")
    x_axis_input = fh.Input(type="text", id="x-axis-input")

    y_axis_text = fh.P("Y Axis Title")
    y_axis_input = fh.Input(type="text", id="y-axis-input")

    plot_button = fh.Button(
        "Plot",
        type="submit",
        hx_post="/get-plot",
        hx_target="#output-div",
        hx_swap="innerHTML",
    )

    plot_selection = fh.Form(
        column_selector_1,
        column_selector_2,
        plot_type_selector,
        title_text,
        title_input,
        x_axis_text,
        x_axis_input,
        y_axis_text,
        y_axis_input,
        plot_button,
        id="plot-selector-form",
    )

    return correlation_button, plot_selection


def create_plot(
    df: pd.DataFrame, type: str, x_col_name: str, y_col_name: str, **kwargs
):
    """
    function that creates a plot of desired type using passed columns.
    It allows further customization using kwargs options.

    Input:
        type (str): scatter, hist, line, or column
        x_col (pd.Series): data that goes on the X axis
        y_col (pd.Series): data that goes on the Y axis
        **kwargs: handles title, x_label, y_label, and legend

    Output:
        (implicit): a plot that will get displayed using HTMX
    """

    fig = plt.figure()
    ax = plt.subplot(1, 1, 1)

    if type == "scatter":
        ax.scatter(df[x_col_name], df[y_col_name])
    if type == "hist":
        ax.hist(df[x_col_name])
    if type == "line":
        ax.plot(df[x_col_name], df[y_col_name])
    if type == "bar-sum":
        temp_df = (
            df[[x_col_name, y_col_name]]
            .groupby(x_col_name, as_index=False)
            .sum()
            .sort_values(by=y_col_name, ascending=False)
        )
        ax.bar(temp_df[x_col_name], height=temp_df[y_col_name])
        del temp_df
    if type == "bar-count":
        temp_df = (
            df[[x_col_name, y_col_name]]
            .groupby(x_col_name, as_index=False)
            .count()
            .sort_values(by=y_col_name, ascending=False)
        )
        ax.bar(temp_df[x_col_name], height=temp_df[y_col_name])
        del temp_df

    ax_params_dict = {
        "title": ax.set_title,
        "x_label": ax.set_xlabel,
        "y_label": ax.set_ylabel,
        "legend": ax.legend,
    }

    for key, value in kwargs.items():
        try:
            ax_params_dict[key](value)
        except:
            pass

    # credit to fh_matplotlib creator for this solution
    bytes_figure = io.BytesIO()
    plt.savefig(bytes_figure, format="jpg")
    bytes_figure.seek(0)
    base64_fig = base64.b64encode(bytes_figure.read()).decode()

    save_data(fig, "current", "jpg")
    # plt.savefig("./figures/current_plot.jpg", format="jpg")

    plt.close(fig)
    plt.close("all")

    return (
        fh.A(
            "Download",
            href=f"data:image/jpg;base64, {base64_fig}",
            download="plot.jpg",
        ),
        fh.Br(),
        fh.Img(src=f"data:image/jpg;base64, {base64_fig}"),
    )
