import discord
from discord.ext import commands
import aiohttp

class Crypto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mapping = {"btc": "bitcoin", "eth": "ethereum", "ltc": "litecoin", "sol": "solana", "doge": "dogecoin"}

    @commands.command(name="crypto", aliases=["price"])
    async def crypto(self, ctx, coin: str):
        """Checks crypto prices (e.g., -crypto btc)."""
        cid = self.mapping.get(coin.lower(), coin.lower())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd"

        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                data = await r.json()
                if cid in data:
                    price = data[cid]['usd']
                    await ctx.send(f"**{cid.title()}** is currently **${price:,.2f} USD**")
                else:
                    await ctx.send("❌ Coin not found.")

async def setup(bot):
    await bot.add_cog(Crypto(bot))