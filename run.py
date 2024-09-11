import pandas as pd
from datetime import datetime, timedelta
import requests
from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer, Input, Button
from textual.containers import Container, Vertical, Horizontal
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich import box
from textual.reactive import reactive
from textual import on
import math
import time
import random
import asyncio
import numpy as np
from src.api_reader import ApiReader
from src.format_date import format_date

SHARK_ASCII = """
[bold cyan]         ,
       .';
   .-'` .'
 ,'    `'        [bold magenta]SharkPool[/]
`.  )  ;         [bold yellow]Ergo Mining Dashboard[/]
  `.  ,' ;
    `'   ;
    _)   )
   /__,'`'
  /   \\`
  \\   /
   \\ /
    V[/]
"""

class WaveWidget(Static):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time = 0.0
        self.wave_chars = "▁▂▃▄▅▆▇██▇▆▅▄▃▂▁"

    def on_mount(self):
        self.set_interval(0.1, self.animate_waves)

    def animate_waves(self):
        self.time += 0.2
        self.refresh()

    def render(self):
        width = self.size.width
        height = 3
        ocean = Text()
        for y in range(height):
            for x in range(width):
                wave1 = math.sin(x * 0.1 + self.time) * 0.5
                wave2 = math.sin(x * 0.2 - self.time * 1.5) * 0.3
                wave = wave1 + wave2
                char_index = int((wave + 1) * (len(self.wave_chars) - 1) / 2)
                char = self.wave_chars[char_index]
                hue = (x / width * 360 + self.time * 50) % 360
                color = f"rgb({self._hsv_to_rgb(hue, 0.7, 0.8)})"
                ocean.append(char, style=color)
            if y < height - 1:
                ocean.append("\n")
        return ocean

    def _hsv_to_rgb(self, h, s, v):
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        return f"{int((r+m)*255)},{int((g+m)*255)},{int((b+m)*255)}"

class DashboardWidget(Static):
    miner_stats = reactive({})

    def compose(self) -> ComposeResult:
        yield Container(
            Static(Panel(self.get_pool_info(), title="[bold magenta]Pool Stats[/]", border_style="cyan", box=box.HEAVY)),
            Static(Panel(self.get_network_info(), title="[bold yellow]Blockchain[/]", border_style="magenta", box=box.HEAVY)),
            
            Static(Panel(self.get_block_info(), title="[bold green]Latest Block[/]", border_style="green", box=box.HEAVY)),
            Static(Panel(self.get_connections_info(), title="[bold cyan]Connections[/]", border_style="yellow", box=box.HEAVY)),
            Static(Panel(self.get_performance_info(), title="[bold blue]Pool Performance[/]", border_style="blue", box=box.HEAVY)),
            Static(Panel(self.get_miner_info(), title="[bold red]Your Miner[/]", border_style="red", box=box.HEAVY), id="miner_info_panel"),
            id="dashboard-container",
            classes="dashboard-container"
        )

    def on_mount(self) -> None:
        self.set_interval(10, self.refresh_data)

    def refresh_data(self) -> None:
        self.refresh(layout=True)

    def update_miner_info(self, miner_stats: dict) -> None:
        self.miner_stats = miner_stats
        self.refresh(layout=True)

    def get_miner_info(self) -> Table:
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold green")
        
        if self.miner_stats:
            table.add_row("Your Hashrate", f"{self.miner_stats.get('current_hashrate', 0) / 1e9:,.2f} Gh/s")
            table.add_row("Shares/Second", f"{self.miner_stats.get('shares_per_second', 0):,.3f}")
            table.add_row("Active Workers", str(self.miner_stats.get('worker_count', 'N/A')))
            
            if self.miner_stats.get('last_block_found'):
                date = format_date(self.miner_stats['last_block_found']['timestamp'])
                table.add_row("Last Block", f"{date}")# (Height: {self.miner_stats['last_block_found']['block_height']})")
                
            table.add_row("Balance", f"{self.miner_stats.get('balance', 0):,.2f} ERG")
            if self.miner_stats.get('last_payment'):
                date = format_date(self.miner_stats['last_payment']['date'])
                table.add_row("Last Payment", f"{self.miner_stats['last_payment']['amount']:,.2f} ERG on {date}")
        else:
            table.add_row("Your Hashrate", "No data")
            table.add_row("Active Workers", "No data")
        
        return table

    def watch_miner_stats(self, old_stats: dict, new_stats: dict) -> None:
        """React to changes in miner_stats."""
        if old_stats != new_stats:
            self.query_one("#miner_info_panel").update(Panel(self.get_miner_info(), title="[bold red]Your Miner[/]", border_style="red", box=box.HEAVY))

    def get_pool_info(self) -> Table:
        reader = ApiReader('../conf')
        pool_data = reader.get_pool_stats()

        p_hash = str(round(pool_data.get('poolhashrate', 0) / 1e9, 2))
        n_miners = str(pool_data.get('connectedminers', 'N/A'))

        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold magenta")
        
        table.add_row("Pool Hashrate", f"{p_hash} Gh/s")
        table.add_row("Miners", n_miners)
        table.add_row("Pool", "SharkPool")
        return table

    def get_network_info(self) -> Table:
        reader = ApiReader('../conf')
        pool_data = reader.get_pool_stats()

        n_hash = str(round(pool_data['networkhashrate'] / 1e12, 2))
        n_diff = str(round(pool_data['networkdifficulty'] / 1e15, 3))
        height = str(pool_data['blockheight'])
      
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold yellow")
        
        table.add_row("Network Hashrate", f"{n_hash} Th/s")
        table.add_row("Network Difficulty", f'{n_diff} P')
        table.add_row("Block Height", height)
        return table

    def get_connections_info(self) -> Table:
        reader = ApiReader('../conf')
        miner_data = reader.get_live_miner_data()
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold magenta")
        table.add_row("POOL URL", '65.108.57.232')
        table.add_row("POOL PORT", '3052')
        counter = 5
        for miner in miner_data:
            addr = miner['address']
            addr = 'Miner: {}...{}'.format(addr[:3], addr[-3:])
            hashrate = '{} Gh/s'.format(round(miner['hashrate'] / 1e9, 2))
            table.add_row(addr, hashrate)
            counter -= 1
            if counter < 0:
                break
        return table

    def get_block_info(self) -> Table:
        reader = ApiReader('../conf')
        pool_data = reader.get_pool_stats()
        
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold green")
        table.add_row("Height", str(pool_data['blockheight']))
        table.add_row("Difficulty", str(round(pool_data['networkdifficulty'] / 1e15, 3)) + ' P')
        table.add_row("Last Found", format_date(pool_data['lastnetworkblocktime']))
        return table

    def get_performance_info(self) -> Table:
        reader = ApiReader('../conf')
        block_data = reader.get_block_stats()
        
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold blue")
        table.add_row("Blocks Found", str(len(block_data)))
        table.add_row("Pool Fee", "1%")
        table.add_row("Payment Threshold", "1 ERG")
        return table

class MinerInputWidget(Static):
    address = reactive("")

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Input(placeholder="Enter your miner address", id="miner_address"),
                id="input_container"
            ),
            Static(id="miner_stats", expand=True)
        )

    def on_mount(self) -> None:
        self.query_one("#miner_address").focus()

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.fetch_miner_stats(event.value)

    def fetch_miner_stats(self, address: str) -> None:
        
        if not address:
            self.query_one("#miner_stats").update("Please enter a miner address.")
            return
        self.query_one("#miner_stats").update(f"Fetching stats for miner: {address}")
        
        try:
            response = requests.get(f'http://37.27.198.175:8000/sigscore/miners/{address}')
            if response.status_code == 200:
                miner_stats = response.json()
                self.query_one("#miner_stats").update(f"Stats updated for miner: {address}")
                
            else:
                self.query_one("#miner_stats").update("No data found for this miner address.")
                miner_stats = None
                
        except Exception as e:
            self.query_one("#miner_stats").update(f"Error fetching miner stats: {str(e)}")
            miner_stats = None
            
        dashboard = self.app.query_one(DashboardWidget)
        dashboard.update_miner_info(miner_stats)
        # 9ehJZvPDgvCNNd2zTQHxnSpcCAtb1kHbEN1VAgeoRD5DPVApYkk


class SharkPoolCyberpunkMonitor(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 1;
        grid-gutter: 0;
        padding: 0;
        background: #000000;
    }
    WaveWidget {
        dock: bottom;
        height: 3;
    }
    #main-container {
        layout: grid;
        grid-size: 3 3;
        grid-gutter: 1 0;  /* Reduced vertical gutter */
    }
    .dashboard-container {
        column-span: 3;
        row-span: 2;
        layout: grid;
        grid-size: 3 2;
        grid-gutter: 1 0;  /* Reduced vertical gutter */
    }
    #miner-input {
        column-span: 2;
    }
    #share-explorer {
        row-span: 2;
    }
    #input_container {
        height: auto;
    }
    #miner_address {
        width: 1fr;
        border: tall $accent;
        background: $boost;
        color: $text;
    }
    #miner_address:focus {
        border: tall $accent-darken-2;
    }
    Static {
        background: $boost;
        color: $text;
        padding: 0 1;  /* Reduced vertical padding */
    }
    Panel {
        background: $boost;
        border: heavy $accent;
        padding: 0 1;  /* Reduced vertical padding */
    }
    Header {
        height: 1;
    }
    Footer {
        height: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            yield DashboardWidget(classes="dashboard-container")
            yield MinerInputWidget(id="miner-input")
        yield WaveWidget()
        yield Footer()

    async def on_mount(self) -> None:
        self.console = Console()
        self.console.print(SHARK_ASCII)
        await asyncio.sleep(3)
        self.console.clear()
        self.set_interval(60, self.refresh_dashboard)

    def refresh_dashboard(self) -> None:
        dashboard = self.query_one(DashboardWidget)
        if dashboard:
            dashboard.refresh(layout=True)

    def update_dashboard_miner_info(self, miner_stats: dict) -> None:
        dashboard = self.query_one(DashboardWidget)
        if dashboard:
            dashboard.refresh(layout=True)

if __name__ == "__main__":
    app = SharkPoolCyberpunkMonitor()
    app.run()