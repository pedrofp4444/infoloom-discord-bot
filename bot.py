import os
import asyncio
import aiosqlite
import aiohttp
import logging
from datetime import datetime, timedelta
from discord.ext import commands, tasks
import discord
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
UCS_API_URL = os.getenv("UCS_API_URL", "https://mei.pedropereira.xyz/api/ucs")
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ucsbot")

intents = discord.Intents.default()
intents.message_content = True  # necessário para prefix commands que leem o conteúdo da mensagem
intents.guilds = True

bot = commands.Bot(command_prefix="+", intents=intents)

DB_PATH = os.getenv("DB_PATH", "subscriptions.db")

# --- helpers para dados ---
async def fetch_ucs():
    async with aiohttp.ClientSession() as session:
        async with session.get(UCS_API_URL) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                logger.error("Erro ao buscar UCS: %s", resp.status)
                return []

def find_uc_by_slug_or_sigla(data, key):
    key_low = key.lower()
    for uc in data:
        if (uc.get("slug","").lower() == key_low) or (uc.get("sigla","").lower() == key_low):
            return uc
    return None

def upcoming_evaluations_for_uc(uc, days):
    now = datetime.utcnow().date()
    end = now + timedelta(days=days)
    out = []
    for a in uc.get("avaliacoes", []):
        try:
            d = datetime.fromisoformat(a["data"]).date()
        except Exception:
            continue
        if now <= d <= end:
            out.append({"data": a["data"], "descricao": a.get("descricao","")})
    return out

# --- DB init ---
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          guild_id TEXT NOT NULL,
          channel_id TEXT NOT NULL,
          uc_slug TEXT NOT NULL,
          days_before INTEGER NOT NULL DEFAULT 7,
          UNIQUE(guild_id, channel_id, uc_slug)
        )
        """)
        await db.commit()

@bot.event
async def on_ready():
    logger.info("Bot conectado como %s", bot.user)
    await init_db()
    check_upcoming.start()

# --- Commands ---
@bot.command(name="ajuda")
async def ajuda(ctx):
    msg = (
        "**Comandos disponíveis:**\n"
        "`+ajuda` - mostra esta mensagem\n"
        "`+proximas [dias]` - lista avaliações nos próximos dias (default 7)\n"
        "`+uc <sigla|slug>` - mostra detalhes de uma UC\n"
        "`+subscrever <slug> [dias-antes]` - subscreve este canal para notificações desta UC\n"
        "`+cancelar <slug>` - remove subscrição desta UC neste canal\n"
        "`+listar` - lista subscrições deste canal\n"
    )
    await ctx.send(msg)

@bot.command(name="proximas")
async def proximas(ctx, days: int = 7):
    data = await fetch_ucs()
    now = datetime.utcnow().date()
    end = now + timedelta(days=days)
    results = []
    for uc in data:
        for a in uc.get("avaliacoes", []):
            try:
                d = datetime.fromisoformat(a["data"]).date()
            except Exception:
                continue
            if now <= d <= end:
                results.append(f"**{uc.get('sigla','?')}** — {a.get('descricao','')} ({a.get('data')})")
    if results:
        await ctx.send("\n".join(results))
    else:
        await ctx.send("🎉 Nenhuma avaliação nos próximos dias.")

@bot.command(name="uc")
async def uc_command(ctx, *, key: str):
    data = await fetch_ucs()
    uc = find_uc_by_slug_or_sigla(data, key)
    if not uc:
        await ctx.send("UC não encontrada.")
        return
    partes = [
        f"**{uc.get('nome')}** ({uc.get('sigla')})",
        f"Perfil: {uc.get('perfil','-')}",
        f"Criterios: {uc.get('criterios','-')}",
        f"Docentes: {'; '.join(uc.get('docentes',[]))}",
        "Próximas avaliações:"
    ]
    avs = upcoming_evaluations_for_uc(uc, 365)
    if avs:
        partes += [f"- {a['descricao']} ({a['data']})" for a in avs]
    else:
        partes.append("Nenhuma avalição encontrada.")
    await ctx.send("\n".join(partes))

@bot.command(name="subscrever")
async def subscrever(ctx, slug: str, days_before: int = 7):
    guild_id = str(ctx.guild.id) if ctx.guild else "dm"
    channel_id = str(ctx.channel.id)
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT OR REPLACE INTO subscriptions (guild_id, channel_id, uc_slug, days_before) VALUES (?, ?, ?, ?)",
                (guild_id, channel_id, slug, days_before)
            )
            await db.commit()
            await ctx.send(f"🔔 Canal subscrito para `{slug}` com aviso `{days_before}` dias antes.")
        except Exception as e:
            logger.exception(e)
            await ctx.send("Erro a subscrever.")

@bot.command(name="cancelar")
async def cancelar(ctx, slug: str):
    guild_id = str(ctx.guild.id) if ctx.guild else "dm"
    channel_id = str(ctx.channel.id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM subscriptions WHERE guild_id=? AND channel_id=? AND uc_slug=?", (guild_id, channel_id, slug))
        await db.commit()
        await ctx.send(f"🚫 Subscrição `{slug}` removida deste canal.")

@bot.command(name="listar")
async def listar(ctx):
    guild_id = str(ctx.guild.id) if ctx.guild else "dm"
    channel_id = str(ctx.channel.id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT uc_slug, days_before FROM subscriptions WHERE guild_id=? AND channel_id=?", (guild_id, channel_id))
        rows = await cur.fetchall()
    if rows:
        msg = "Subscrições deste canal:\n" + "\n".join([f"- {r[0]} (aviso {r[1]} dias antes)" for r in rows])
    else:
        msg = "Nenhuma subscrição neste canal."
    await ctx.send(msg)

# --- Periodic check: notifica canais subscritos ---
@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_upcoming():
    logger.info("Verificação periódica: buscar subscrições e UCS")
    data = await fetch_ucs()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT guild_id, channel_id, uc_slug, days_before FROM subscriptions")
        rows = await cur.fetchall()
    if not rows:
        return
    # Agrupa por uc_slug
    uc_map = { (uc.get("slug") or uc.get("sigla")): uc for uc in data for _ in (0,) }
    # Simples: iterar e notificar conforme necessidade
    for guild_id, channel_id, uc_slug, days_before in rows:
        uc = find_uc_by_slug_or_sigla(data, uc_slug)
        if not uc:
            continue
        upcoming = upcoming_evaluations_for_uc(uc, int(days_before))
        if not upcoming:
            continue
        # Criar mensagem e enviar
        chan = bot.get_channel(int(channel_id))
        if not chan:
            logger.warning("Canal %s não encontrado (bot talvez não tenha acesso).", channel_id)
            continue
        txt = f"🔔 **Notificação - {uc.get('sigla','')}**\n"
        txt += "\n".join([f"- {a['descricao']} ({a['data']})" for a in upcoming])
        try:
            await chan.send(txt)
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.exception("Erro a enviar notificação para %s: %s", channel_id, e)

# --- Run ---
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
