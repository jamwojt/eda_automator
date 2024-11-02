import io

import pandas as pd
from fasthtml import common as fh
import uvicorn

import util_funcs as uf


CSS_style = (
    "#plot-setup-div{width: 50%}"
    "#welcome-sign{text-align: center}"
    "#output-div{text-align: center;margin-top: 30px}"
    "#correlation-button{width: 100%}"
)
gridlink = fh.Link(
    rel="stylesheet",
    href="https://cdnjs.cloudflare.com/ajax/libs/flexboxgrid/6.3.1/flexboxgrid.min.css",
    type="text/css",
)
GRID_CLS = "box col-xs-12 col-sm-12 col-md-6 col-lg-6"

css = fh.Style(f":root {CSS_style}")
app = fh.FastHTML(hdrs=(fh.picolink, css, gridlink))


@app.route("/", methods=["get"])
def home():
    welcome_sign = fh.Div(fh.H1("File analyzer"), id="welcome-sign")
    upload_form = fh.Form(
        fh.Input(type="file", id="file-input"),
        fh.Button("Upload", type="submit"),
        id="input-form",
        hx_post="/load-file",
        hx_target="#column-selector",
        enctype="multipart/form-data",
    )

    file_selector_waiting_room = fh.P(id="column-selector", hx_swap_oob="outerHTML")

    plot_setup = fh.Div(
        upload_form, file_selector_waiting_room, id="plot-setup-div", cls=GRID_CLS
    )

    image_placeholder = fh.Div(fh.Img(id="plot-image"), id="output-div", cls=GRID_CLS)

    main_div = fh.Div(plot_setup, image_placeholder, cls="row")

    return fh.Title("File analyzer"), welcome_sign, main_div


@app.route("/load-file", methods=["post"])
async def load_file(request: fh.Request):
    response = await request.form()
    file_content = await response.get("file-input").read()
    global df
    df = pd.read_csv(io.BytesIO(file_content))
    headers = list(df.columns)

    selectors = uf.get_plot_selectors(headers)

    return selectors


@app.route("/get-correlation", methods=["post"])
def get_correlation():
    corr_df = uf.get_correlation_df(df)

    csv_file = io.StringIO()
    corr_df.to_csv(csv_file, index=False)
    uf.save_data(corr_df, "corr", "csv")
    csv_file.seek(0)

    return fh.Div(
        fh.A(
            "Download",
            href=f"data:text/csv;text, {csv_file.read()}",
            download="corr.csv",
        ),
        fh.Br(),
        fh.NotStr(corr_df.to_html()),
    )


@app.route("/get-plot", methods=["post"])
async def plot_data(request: fh.Request):
    response = await request.form()
    request_values = uf.get_items_from_request(
        response,
        "column-selector-1",
        "column-selector-2",
        "plot-type-selector",
        "title-input",
        "x-axis-input",
        "y-axis-input",
    )

    return fh.Div(
        uf.create_plot(
            df,
            request_values["plot-type-selector"],
            request_values["column-selector-1"],
            request_values["column-selector-2"],
            title=request_values["title-input"],
            x_label=request_values["x-axis-input"],
            y_label=request_values["y-axis-input"],
        ),
        id="output-div",
        cls="box",
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
