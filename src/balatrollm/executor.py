"""Task execution for BalatroLLM runs."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from balatrobot import BalatroInstance
from balatrobot import Config as BalatrobotConfig

from .bot import Bot
from .client import BalatroClient
from .config import Config, Task


@dataclass
class Executor:
    """Executes tasks with parallelism."""

    config: Config
    tasks: list[Task]
    runs_dir: Path = field(default_factory=Path.cwd)

    _instances: dict[int, BalatroInstance] = field(
        default_factory=dict, init=False, repr=False
    )
    _port_pool: asyncio.Queue[int] = field(
        default_factory=asyncio.Queue, init=False, repr=False
    )
    _shutdown: asyncio.Event = field(
        default_factory=asyncio.Event, init=False, repr=False
    )

    async def run(self) -> None:
        """Execute all tasks."""
        ports = range(self.config.port, self.config.port + self.config.parallel)
        try:
            await self._start_instances(ports)
            await self._execute_tasks()
        except asyncio.CancelledError:
            print("\nInterrupted! Cleaning up...")
            raise
        finally:
            await self._stop_instances()
        print("Done.")

    async def _start_instances(self, ports: range) -> None:
        """Start Balatro instances."""
        cfg = BalatrobotConfig.from_env()

        # Generate single session_id for all instances (prevents split directories)
        session_id = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

        # Create all instances with shared session_id
        instances = []
        for port in ports:
            instance = BalatroInstance(cfg, session_id=session_id, port=port)
            instances.append((port, instance))

        # Start all instances in parallel
        await asyncio.gather(*(instance.start() for _, instance in instances))

        # Register instances in pool
        for port, instance in instances:
            self._instances[port] = instance
            await self._port_pool.put(port)

    async def _stop_instances(self) -> None:
        """Stop all instances."""
        await asyncio.gather(
            *(i.stop() for i in self._instances.values()),
            return_exceptions=True,
        )
        self._instances.clear()

    async def _execute_tasks(self) -> None:
        """Execute tasks with port pool."""
        total = len(self.tasks)
        count = 0

        async def run_task(task: Task) -> None:
            nonlocal count
            if self._shutdown.is_set():
                return
            port = await self._port_pool.get()
            try:
                count += 1
                instance = self._instances[port]
                log_path = instance.log_path
                print(
                    f"[{count:0{len(str(total))}d}/{total}] STARTED   | {log_path} | {task}"
                )
                bot = Bot(task=task, config=self.config, port=port)
                async with bot:
                    await bot.play(self.runs_dir)
                print(
                    f"[{count:0{len(str(total))}d}/{total}] COMPLETED | {log_path} | {task}"
                )
            except Exception:
                print(
                    f"[{count:0{len(str(total))}d}/{total}] ERROR     | {log_path} | {task}"
                )
            finally:
                # Reset game to menu state before returning port to pool
                try:
                    async with BalatroClient(
                        host=self.config.host, port=port
                    ) as reset_client:
                        await reset_client.call("menu")
                        await asyncio.sleep(0.5)
                except Exception:
                    pass  # Best effort - continue even if reset fails
                await self._port_pool.put(port)

        pending = [asyncio.create_task(run_task(t)) for t in self.tasks]
        try:
            await asyncio.gather(*pending, return_exceptions=True)
        except asyncio.CancelledError:
            self._shutdown.set()
            for t in pending:
                t.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            raise
