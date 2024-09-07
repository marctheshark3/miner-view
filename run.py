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
            Static(Panel(self.get_connections_info(), title="[bold cyan]Connections[/]", border_style="yellow", box=box.HEAVY)),
            Static(Panel(self.get_block_info(), title="[bold green]Latest Block[/]", border_style="green", box=box.HEAVY)),
            Static(Panel(self.get_performance_info(), title="[bold blue]Pool Performance[/]", border_style="blue", box=box.HEAVY)),
            Static(Panel(self.get_miner_info(), title="[bold red]Your Miner[/]", border_style="red", box=box.HEAVY), id="miner_info_panel"),
            id="dashboard-container",
            classes="dashboard-container"
        )

    def watch_miner_stats(self, old_stats, new_stats):
        if new_stats != old_stats:
            miner_panel = self.query_one("#miner_info_panel")
            miner_panel.update(Panel(self.get_miner_info(), title="[bold red]Your Miner[/]", border_style="red", box=box.HEAVY))

    def get_miner_info(self) -> Table:
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold green")
        
        if self.miner_stats:
            table.add_row("Your Hashrate", f"{self.miner_stats['total_hashrate'] / 1e6:,.2f} Gh/s")
            try:
                table.add_row("Last Updated", self.miner_stats['timestamp'].strftime('%Y-%m-%d %H:%M:%S'))
            except Exception:
                table.add_row("Last Updated", str(self.miner_stats['timestamp']))
            table.add_row("Active Workers", str(self.miner_stats['n_workers']))
            for worker in self.miner_stats['workers']:
                table.add_row("Worker:", worker)
        else:
            table.add_row("Your Hashrate", "No data")
            table.add_row("Active Workers", "No data")
            table.add_row("Last Updated", "Never")
        
        return table

    def on_mount(self):
        self.set_interval(10, self.refresh_data)

    def refresh_data(self):
        self.refresh(layout=True)

    def get_pool_info(self) -> Table:
        reader = ApiReader('../conf')
        pool_data = reader.get_pool_stats()

        p_hash = str(round(pool_data['poolhashrate'] / 1e6, 2))
        n_miners = str(pool_data['connectedminers'])

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
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold magenta")
        table.add_row("POOL URL", '65.108.57.232')
        table.add_row("POOL PORT", '3052')
        return table

    def get_block_info(self) -> Table:
        reader = ApiReader('../conf')
        pool_data = reader.get_pool_stats()
        
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold green")
        table.add_row("Height", str(pool_data['blockheight']))
        table.add_row("Difficulty", str(round(pool_data['networkdifficulty'] / 1e15, 3)) + ' P')
        table.add_row("Last Found", pool_data['lastnetworkblocktime'])
        return table

    def get_performance_info(self) -> Table:
        reader = ApiReader('../conf')
        block_data = reader.get_block_stats()
        
        table = Table(show_header=False, expand=True, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold blue")
        table.add_row("Blocks Found (24h)", str(len(block_data)))
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

    def on_mount(self):
        self.query_one("#miner_address").focus()

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted):
        self.fetch_miner_stats(event.value)

    def fetch_miner_stats(self, address):
        if not address:
            self.query_one("#miner_stats").update("Please enter a miner address.")
            return

        self.query_one("#miner_stats").update(f"Fetching stats for miner: {address}")
        
        try:
            response = requests.get(f'http://37.27.198.175:8000/miningcore/minerstats')
            data = response.json()
            df = pd.DataFrame(data)
            if address in list(df.miner.unique()):
                df = df[df.miner == address]
                df['created'] = pd.to_datetime(df['created'])
                
                df = df.sort_values('created', ascending=False)
                
                latest_timestamp = df['created'].iloc[0]
                latest_data = df[df['created'] == latest_timestamp]
                total_hashrate = latest_data['hashrate'].sum()
                
                latest_miner_stats = {
                    'address': address,
                    'timestamp': latest_timestamp,
                    'total_hashrate': total_hashrate,
                    'n_workers': len(latest_data),
                    'workers': latest_data.worker.unique().tolist()
                }
                
                # Update the dashboard and the ShareExplorerWidget
                self.app.update_dashboard_miner_info(latest_miner_stats)
                self.query_one("#miner_stats").update(f"Stats updated for miner: {address}")
                
            else:
                self.query_one("#miner_stats").update("No data found for this miner address.")
                latest_miner_stats = None
                
        except Exception as e:
            self.query_one("#miner_stats").update(f"Error fetching miner stats: {str(e)}")
            latest_miner_stats = None

        # Update the share explorer widget based on the latest miner stats
        self.app.update_dashboard_miner_info(latest_miner_stats)


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

    def refresh_dashboard(self):
        dashboard = self.query_one(DashboardWidget)
        if dashboard:
            dashboard.refresh(layout=True)

    def update_dashboard_miner_info(self, miner_stats):
        dashboard = self.query_one(DashboardWidget)
        if dashboard and miner_stats:
            dashboard.miner_stats = miner_stats
        elif dashboard:
            dashboard.miner_stats = {}


if __name__ == "__main__":
    app = SharkPoolCyberpunkMonitor()
    app.run()