import discord
from discord.ext import commands
import aiohttp

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Configuration for each coin
        self.coin_config = {
            "btc": {
                "name": "bitcoin",
                "display": "Bitcoin",
                "symbol": "BTC",
                "api": "https://api.blockcypher.com/v1/btc/main/addrs/{}/balance",
                "unit": 100_000_000,  # Satoshis
                "color": 0xF7931A,
                "icon": "https://cryptologos.cc/logos/bitcoin-btc-logo.png"
            },
            "ltc": {
                "name": "litecoin",
                "display": "Litecoin",
                "symbol": "LTC",
                "api": "https://api.blockcypher.com/v1/ltc/main/addrs/{}/balance",
                "unit": 100_000_000,  # Satoshis
                "color": 0x345D9D,
                "icon": "https://cryptologos.cc/logos/litecoin-ltc-logo.png"
            },
            "eth": {
                "name": "ethereum",
                "display": "Ethereum",
                "symbol": "ETH",
                "api": "https://api.blockcypher.com/v1/eth/main/addrs/{}/balance",
                "unit": 1_000_000_000_000_000_000,  # Wei
                "color": 0x3C3C3D,
                "icon": "https://cryptologos.cc/logos/ethereum-eth-logo.png"
            }
        }

    @commands.command(name="bal", aliases=["walletbal", "check"])
    async def balance(self, ctx, coin: str = None, address: str = None):
        """Fetches balance for BTC, LTC, or ETH wallets."""

        # 1. Validation
        if not coin or not address:
            return await ctx.send("❌ **Usage:** `-bal <btc/ltc/eth> <address>`")

        coin_key = coin.lower()
        if coin_key not in self.coin_config:
            return await ctx.send("❌ Invalid coin! Use **btc**, **ltc**, or **eth**.")

        config = self.coin_config[coin_key]

        async with aiohttp.ClientSession() as session:
            # 2. Fetch Wallet Balance
            async with session.get(config["api"].format(address)) as resp:
                if resp.status != 200:
                    return await ctx.send(f"❌ **Error:** Could not find that {config['display']} address.")
                data = await resp.json()

            # 3. Fetch current USD Price (Bonus feature)
            price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={config['name']}&vs_currencies=usd"
            usd_price = 0
            async with session.get(price_url) as p_resp:
                if p_resp.status == 200:
                    p_data = await p_resp.json()
                    usd_price = p_data.get(config['name'], {}).get('usd', 0)

            # 4. Calculations
            # Convert from Satoshis/Wei to whole coins
            confirmed = data['balance'] / config['unit']
            unconfirmed = data['unconfirmed_balance'] / config['unit']
            total = confirmed + unconfirmed
            usd_value = total * usd_price

            # 5. Build the Embed
            embed = discord.Embed(
                title=f"{config['display']} Wallet Info",
                description=f"Address: `{address}`",
                color=config['color']
            )
            embed.set_thumbnail(url=config['icon'])

            embed.add_field(name="Confirmed Balance", value=f"**{confirmed:.8f} {config['symbol']}**", inline=True)

            if unconfirmed != 0:
                embed.add_field(name="Pending", value=f"**{unconfirmed:.8f} {config['symbol']}**", inline=True)

            if usd_price > 0:
                embed.add_field(name="USD Value", value=f"**${usd_value:,.2f} USD**", inline=False)

            embed.set_footer(text=f"Live Price: ${usd_price:,.2f} | Powered by BlockCypher API")

            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Balance(bot))