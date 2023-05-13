import io

import pandas as pd

import matplotlib.pyplot as plt

from flask import Flask, Response

import db

app = Flask(__name__)

@app.route('/plot.png')
def plot_png():
    # Generate data
    data = pd.Series([1, 2, 3, 4, 5])

    # Create plot
    # fig, ax = plt.subplots()
    # ax.plot(data)

    plt.bar(data.index, data.values)

    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Return plot as image response
    return Response(buf.getvalue(), mimetype='image/png')

if __name__ == '__main__':
    app.run("0.0.0.0")
