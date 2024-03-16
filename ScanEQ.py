import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import yfinance as yf
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
import re
from datetime import datetime

# Define trading strategies
class MACS(Strategy):
    def init(self):
        price = self.data.Close
        self.sma1 = self.I(SMA, price, 10)
        self.sma2 = self.I(SMA, price, 20)

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.sell()

class BollingerBands(Strategy):
    def init(self):
        close = pd.Series(self.data.Close)
        self.n = 20
        self.k = 2
        self.sma = close.rolling(window=self.n).mean()
        stddev = close.rolling(window=self.n).std()
        self.upper_band = self.sma + (self.k * stddev)
        self.lower_band = self.sma - (self.k * stddev)
        self.upper_band = self.I(lambda x: self.upper_band, self.data.Close)
        self.lower_band = self.I(lambda x: self.lower_band, self.data.Close)

    def next(self):
        if not self.position:
            if self.data.Close[-1] > self.upper_band[-1]:
                self.sell()
            elif self.data.Close[-1] < self.lower_band[-1]:
                self.buy()
        else:
            if self.position.is_long and self.data.Close[-1] > self.upper_band[-1]:
                self.position.close()
            elif self.position.is_short and self.data.Close[-1] < self.lower_band[-1]:
                self.position.close()

# Input Validation Functions
def validate_ticker(ticker):
    if re.match("^[a-zA-Z0-9.-]{1,10}$", ticker):
        return True
    else:
        tk.messagebox.showerror("Invalid Ticker", "Ticker symbol is invalid.")
        return False

def validate_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        tk.messagebox.showerror("Invalid Date", "Date should be in YYYY-MM-DD format.")
        return False

# GUI Application
class MyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Backtesting Application")
        self.create_widgets()

    def create_widgets(self):
        self.ticker_label = ttk.Label(self.root, text="Ticker:")
        self.ticker_label.grid(row=0, column=0, padx=5, pady=5)
        self.ticker_entry = ttk.Entry(self.root)
        self.ticker_entry.grid(row=0, column=1, padx=5, pady=5)

        self.start_date_label = ttk.Label(self.root, text="Start Date (YYYY-MM-DD):")
        self.start_date_label.grid(row=1, column=0, padx=5, pady=5)
        self.start_date_entry = ttk.Entry(self.root)
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=5)

        self.end_date_label = ttk.Label(self.root, text="End Date (YYYY-MM-DD):")
        self.end_date_label.grid(row=2, column=0, padx=5, pady=5)
        self.end_date_entry = ttk.Entry(self.root)
        self.end_date_entry.grid(row=2, column=1, padx=5, pady=5)

        self.download_button = ttk.Button(self.root, text="Download Data", command=self.download_data)
        self.download_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        self.MACS_button = ttk.Button(self.root, text="MACS Strategy", command=lambda: self.plot_strategy(MACS))
        self.MACS_button.grid(row=4, column=0, padx=5, pady=5)

        self.Bollinger_button = ttk.Button(self.root, text="Bollinger Bands Strategy", command=lambda: self.plot_strategy(BollingerBands))
        self.Bollinger_button.grid(row=4, column=1, padx=5, pady=5)

    def download_data(self):
        ticker = self.ticker_entry.get()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()

        if not (validate_ticker(ticker) and validate_date(start_date) and validate_date(end_date)):
            return  # Stop execution if any input is invalid

        df = yf.download(ticker, start=start_date, end=end_date)
        if not df.empty:
            df.to_csv(f"{ticker}_data.csv")
            messagebox.showinfo("Download", f"Data for {ticker} downloaded successfully.")
        else:
            messagebox.showerror("Error", "Failed to download data.")

    def plot_strategy(self, strategy_class):
        ticker = self.ticker_entry.get()
        if not validate_ticker(ticker):  # Additional validation before plotting
            return

        try:
            df = pd.read_csv(f"{ticker}_data.csv", index_col='Date', parse_dates=True)
        except FileNotFoundError:
            messagebox.showerror("Error", f"No data file found for ticker {ticker}. Please download data first.")
            return

        bt = Backtest(df, strategy_class, cash=10000, commission=.002)
        stats = bt.run()
        bt.plot()

if __name__ == "__main__":
    root = tk.Tk()
    app = MyApp(root)
    root.mainloop()
