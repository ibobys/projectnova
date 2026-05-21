"""
╔══════════════════════════════════════════════════════════════════╗
║              PROJECT NOVA — Discord Bot  (Python)                ║
║                      Tek dosya: main.py                          ║
║                   Railway Variables üzerinden çalışır            ║
╚══════════════════════════════════════════════════════════════════╝

Railway → Projen → Variables kısmına şunları ekle:
    BOT_TOKEN  = discord bot tokenin
    CLIENT_ID  = uygulama id
    GUILD_ID   = sunucu id
"""

import os
import asyncio
import discord
from discord.ext import commands, tasks
from discord import option

# ══════════════════════════════════════════════════════════════════
#  CONFIG — Railway Variables'tan otomatik okunur
# ══════════════════════════════════════════════════════════════════
TOKEN = os.getenv("TOKEN")
CLIENT_ID = int(os.getenv("CLIENT_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))

VERIFIED_ROLE_ID      = 1482031063936139264   # Doğrulama rolü
ANNOUNCEMENT_CH_ID    = 1482021925319344409   # Duyuru kanalı
PARTNER_CH_ID         = 1482021699020132486   # Partner başvuru kanalı
REQUEST_CH_ID         = 1482034060678140015   # İstek/öneri kanalı
TICKET_CATEGORY_ID    = None                  # Ticket kategorisi (None = kategorisiz)

BANNED_WORDS = [
    "küfür1", "küfür2", "orospu", "sik", "göt", "amk", "amına",
    "bok", "piç", "oç", "siktir", "fuck", "shit", "bitch",
    "asshole", "bastard",
]

# ══════════════════════════════════════════════════════════════════
#  BOT SETUP
# ══════════════════════════════════════════════════════════════════
intents = discord.Intents.default()
intents.members        = True
intents.message_content = True
intents.presences      = True

bot = commands.Bot(
    intents=intents,
    debug_guilds=[GUILD_ID],   # Slash komutları anında bu sunucuya yüklenir
)

# Açık ticketları takip et  { user_id: channel_id }
open_tickets: dict[int, int] = {}


# ══════════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════
def nova_embed(
    title: str,
    description: str,
    color: discord.Color = discord.Color.blurple(),
) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_author(name="Project Nova")
    embed.set_footer(text="Project Nova • Bot Sistemi")
    embed.timestamp = discord.utils.utcnow()
    return embed


def contains_banned(text: str) -> bool:
    low = text.lower()
    return any(w in low for w in BANNED_WORDS)


# ══════════════════════════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅  {bot.user} olarak giriş yapıldı!")
    update_activity.start()


@tasks.loop(minutes=1)
async def update_activity():
    guild = bot.get_guild(GUILD_ID)
    if guild:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{guild.member_count} Üye ile Büyüyoruz 🚀",
            )
        )


# ══════════════════════════════════════════════════════════════════
#  KÜFÜR FİLTRESİ
# ══════════════════════════════════════════════════════════════════
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    if contains_banned(message.content):
        try:
            await message.delete()
            warn = await message.channel.send(
                embed=nova_embed(
                    "🚫 Küfür Engellendi",
                    f"{message.author.mention}, sunucu kurallarımız gereği **küfür ve hakaret** içeren "
                    f"ifadeler yasaktır.\n\nBu mesaj otomatik olarak silindi. Lütfen saygılı bir dil "
                    f"kullanın.\n\n⚠️ Tekrarlanması durumunda moderasyon işlemi uygulanacaktır.",
                    discord.Color.red(),
                )
            )
            await asyncio.sleep(8)
            await warn.delete()
        except Exception as e:
            print(f"Küfür silme hatası: {e}")
    await bot.process_commands(message)


# ══════════════════════════════════════════════════════════════════
#  /ticket-kur
# ══════════════════════════════════════════════════════════════════
@bot.slash_command(name="ticket-kur", description="📋 Ticket sistemini kurarak destek merkezi panelini gönderir.")
@commands.has_permissions(administrator=True)
async def ticket_kur(ctx: discord.ApplicationContext):
    options = [
        discord.SelectOption(label="Sipariş",            description="Yeni bir sipariş vermek istiyorum",          value="siparis",       emoji="⭐"),
        discord.SelectOption(label="Destek",             description="Bir sorunum var, yardım istiyorum",          value="destek",        emoji="🌟"),
        discord.SelectOption(label="Proje İsteği",       description="Özel proje talebi oluşturmak istiyorum",     value="proje_istegi",  emoji="💫"),
        discord.SelectOption(label="Ücretsiz Proje Alma",description="Ücretsiz proje hakkında bilgi almak istiyorum",value="ucretsiz_proje",emoji="✨"),
        discord.SelectOption(label="Diğer",              description="Diğer konular hakkında",                     value="diger",         emoji="🔮"),
    ]
    select = discord.ui.Select(
        placeholder="📂 Bir kategori seç...",
        options=options,
        custom_id="ticket_select",
    )

    async def ticket_select_cb(interaction: discord.Interaction):
        await handle_ticket_select(interaction, select.values[0])

    select.callback = ticket_select_cb

    view = discord.ui.View(timeout=None)
    view.add_item(select)

    embed = discord.Embed(
        title="🎫  Destek Merkezi",
        description=(
            "**🧭 Destek Merkezi Hakkında.**\n"
            "Aşağıdaki seçeneklerden uygun olanı seçerek hemen bir ticket oluşturabilirsiniz.\n\n"
            "**📌 Sunucu Bilgisi.**\n"
            "Gereksiz ticket açmayın, Sunucu Kurallarını Okumayı Unutmayın."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_author(name="Project Nova")
    embed.set_footer(text="Project Nova • Ticket Sistemi")
    embed.timestamp = discord.utils.utcnow()

    await ctx.channel.send(embed=embed, view=view)
    await ctx.respond("✅ Ticket paneli başarıyla gönderildi!", ephemeral=True)


async def handle_ticket_select(interaction: discord.Interaction, value: str):
    guild = interaction.guild
    user  = interaction.user

    if user.id in open_tickets:
        ch = guild.get_channel(open_tickets[user.id])
        if ch:
            await interaction.response.send_message(
                embed=nova_embed(
                    "⚠️ Zaten Açık Ticket Var",
                    f"Zaten açık bir ticketin mevcut: {ch.mention}\nLütfen önce mevcut ticketini kapat.",
                    discord.Color.orange(),
                ),
                ephemeral=True,
            )
            return

    labels = {
        "siparis":       "📦 Sipariş",
        "destek":        "🛠️ Destek",
        "proje_istegi":  "💻 Proje İsteği",
        "ucretsiz_proje":"🎁 Ücretsiz Proje",
        "diger":         "📌 Diğer",
    }
    label = labels.get(value, "Ticket")
    ch_name = f"ticket-{user.name[:12].lower()}-{str(user.id)[-4:]}"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }

    try:
        category = guild.get_channel(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID else None
        ticket_ch = await guild.create_text_channel(
            name=ch_name,
            overwrites=overwrites,
            category=category,
        )
        open_tickets[user.id] = ticket_ch.id

        close_btn = discord.ui.Button(
            label="🔒 Ticketi Kapat",
            style=discord.ButtonStyle.danger,
            custom_id=f"ticket_close_{ticket_ch.id}",
        )

        async def close_cb(i: discord.Interaction):
            embed_c = nova_embed(
                "🔒 Ticket Kapatılıyor",
                f"Bu ticket **{i.user}** tarafından kapatıldı.\nKanal 5 saniye içinde silinecek.",
                discord.Color.red(),
            )
            await i.response.send_message(embed=embed_c)
            # Ticket map'ten kaldır
            for uid, cid in list(open_tickets.items()):
                if cid == ticket_ch.id:
                    del open_tickets[uid]
                    break
            await asyncio.sleep(5)
            await ticket_ch.delete()

        close_btn.callback = close_cb
        close_view = discord.ui.View(timeout=None)
        close_view.add_item(close_btn)

        ticket_embed = discord.Embed(
            title=f"{label} — Ticket Açıldı",
            description=(
                f"Merhaba {user.mention}! 👋\n\n"
                f"**Project Nova Destek Ekibine** hoş geldiniz.\n\n"
                f"📋 **Ticket Konusu:** {label}\n"
                f"👤 **Açan:** {user}\n"
                f"📅 **Açılış:** {discord.utils.format_dt(discord.utils.utcnow(), 'F')}\n\n"
                f"Lütfen sorununuzu veya talebinizi detaylı olarak açıklayın. "
                f"Ekibimiz en kısa sürede size yardımcı olacaktır.\n\n"
                f"⏱️ Ortalama yanıt süremiz **15-30 dakika**'dır."
            ),
            color=discord.Color.blurple(),
        )
        ticket_embed.set_author(name="Project Nova")
        ticket_embed.set_footer(text="Project Nova • Ticket Sistemi")
        ticket_embed.timestamp = discord.utils.utcnow()

        await ticket_ch.send(content=user.mention, embed=ticket_embed, view=close_view)

        await interaction.response.send_message(
            embed=nova_embed(
                "✅ Ticket Oluşturuldu!",
                f"Ticketin başarıyla oluşturuldu! {ticket_ch.mention}\nSeni yönlendirdik, lütfen kanalı kontrol et.",
                discord.Color.green(),
            ),
            ephemeral=True,
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Ticket oluşturulamadı: {e}", ephemeral=True)


# ══════════════════════════════════════════════════════════════════
#  /dogrulama
# ══════════════════════════════════════════════════════════════════
@bot.slash_command(name="dogrulama", description="✅ Doğrulama panelini gönderir.")
@commands.has_permissions(administrator=True)
async def dogrulama(ctx: discord.ApplicationContext):
    verify_btn = discord.ui.Button(
        label="✅  Doğrulamak İçin Tıkla",
        style=discord.ButtonStyle.success,
        custom_id="verify_btn",
    )

    async def verify_cb(interaction: discord.Interaction):
        role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        if not role:
            await interaction.response.send_message("❌ Doğrulama rolü bulunamadı.", ephemeral=True)
            return
        member = interaction.user
        if role in member.roles:
            await interaction.response.send_message(
                embed=nova_embed("✅ Zaten Doğrulandın!", "Zaten doğrulama rolüne sahipsin. Sunucunun tadını çıkar! 🎉", discord.Color.green()),
                ephemeral=True,
            )
            return
        try:
            await member.add_roles(role)
            await interaction.response.send_message(
                embed=nova_embed(
                    "✅ Doğrulama Başarılı!",
                    f"Merhaba **{member.display_name}**! 🎉\n\n"
                    f"Doğrulaman tamamlandı ve sunucuya tam erişim sağladın.\n\n"
                    f"🌟 **Project Nova**'ya hoş geldin!",
                    discord.Color.green(),
                ),
                ephemeral=True,
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Rol verilemedi: {e}", ephemeral=True)

    verify_btn.callback = verify_cb
    view = discord.ui.View(timeout=None)
    view.add_item(verify_btn)

    embed = discord.Embed(
        title="🔐  Doğrulama Sistemi",
        description=(
            "**Project Nova'ya Hoş Geldiniz!**\n\n"
            "Sunucumuza tam erişim sağlamak için aşağıdaki butona tıklayarak kimliğinizi doğrulayın.\n\n"
            "✅ Doğruladıktan sonra tüm kanallara erişebileceksiniz.\n\n"
            "⚠️ Doğrulama yapmadan sunucu içeriğine erişemezsiniz."
        ),
        color=discord.Color.green(),
    )
    embed.set_author(name="Project Nova")
    embed.set_footer(text="Project Nova • Doğrulama Sistemi")
    embed.timestamp = discord.utils.utcnow()

    await ctx.channel.send(embed=embed, view=view)
    await ctx.respond("✅ Doğrulama paneli başarıyla gönderildi!", ephemeral=True)


# ══════════════════════════════════════════════════════════════════
#  /dogrula  (admin — manuel)
# ══════════════════════════════════════════════════════════════════
@bot.slash_command(name="dogrula", description="🛡️ Belirtilen kullanıcıya manuel olarak doğrulama rolü ver.")
@commands.has_permissions(administrator=True)
@option("kullanıcı", discord.Member, description="Doğrulanacak kullanıcıyı seçin.")
async def dogrula(ctx: discord.ApplicationContext, kullanıcı: discord.Member):
    role = ctx.guild.get_role(VERIFIED_ROLE_ID)
    if not role:
        await ctx.respond("❌ Doğrulama rolü bulunamadı.", ephemeral=True)
        return
    try:
        await kullanıcı.add_roles(role)
        await ctx.respond(
            embed=nova_embed(
                "✅ Manuel Doğrulama",
                f"{kullanıcı.mention} kullanıcısına başarıyla **doğrulama rolü** verildi.\n\n"
                f"👤 İşlemi yapan: {ctx.author.mention}\n"
                f"🕐 Tarih: {discord.utils.format_dt(discord.utils.utcnow(), 'F')}",
                discord.Color.green(),
            ),
            ephemeral=True,
        )
    except Exception as e:
        await ctx.respond(f"❌ Rol verilemedi: {e}", ephemeral=True)


# ══════════════════════════════════════════════════════════════════
#  /duyuru-paylas
# ══════════════════════════════════════════════════════════════════
@bot.slash_command(name="duyuru-paylas", description="📣 Duyuru kanalına mesaj gönderir.")
@commands.has_permissions(administrator=True)
@option("metin", str, description="Duyuruda yayınlanacak metni girin.")
async def duyuru_paylas(ctx: discord.ApplicationContext, metin: str):
    ch = bot.get_channel(ANNOUNCEMENT_CH_ID)
    if not ch:
        await ctx.respond("❌ Duyuru kanalı bulunamadı.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📣  Yeni Duyuru",
        description=metin,
        color=discord.Color.gold(),
    )
    embed.set_author(name="Project Nova Duyuru")
    embed.set_footer(text=f"Duyuruyu yapan: {ctx.author}")
    embed.timestamp = discord.utils.utcnow()

    await ch.send(content="@everyone", embed=embed)
    await ctx.respond(f"✅ Duyuru <#{ANNOUNCEMENT_CH_ID}> kanalına başarıyla gönderildi!", ephemeral=True)


# ══════════════════════════════════════════════════════════════════
#  /ban
# ══════════════════════════════════════════════════════════════════
@bot.slash_command(name="ban", description="🔨 Belirtilen kullanıcıyı sunucudan kalıcı olarak yasaklar.")
@commands.has_permissions(ban_members=True)
@option("kullanıcı", discord.Member, description="Banlanacak kullanıcıyı seçin.")
@option("sebep", str, description="Banlama sebebini girin.", required=False, default="Sebep belirtilmedi.")
async def ban(ctx: discord.ApplicationContext, kullanıcı: discord.Member, sebep: str):
    if not kullanıcı.guild_permissions.administrator is False and kullanıcı.top_role >= ctx.author.top_role:
        await ctx.respond("❌ Bu kullanıcıyı banlayamazsın. Rolü senden üstte.", ephemeral=True)
        return
    try:
        await kullanıcı.ban(reason=f"{ctx.author} tarafından: {sebep}")
        embed = discord.Embed(title="🔨  Kullanıcı Banlandı", color=discord.Color.red())
        embed.set_author(name="Project Nova • Moderasyon")
        embed.add_field(name="👤 Kullanıcı",   value=f"{kullanıcı} ({kullanıcı.id})", inline=True)
        embed.add_field(name="🛡️ Moderatör",  value=str(ctx.author),                 inline=True)
        embed.add_field(name="📋 Sebep",        value=sebep,                           inline=False)
        embed.add_field(name="📅 Tarih",        value=discord.utils.format_dt(discord.utils.utcnow(), "F"), inline=False)
        embed.set_thumbnail(url=kullanıcı.display_avatar.url)
        embed.set_footer(text="Project Nova • Moderasyon Sistemi")
        embed.timestamp = discord.utils.utcnow()
        await ctx.respond(embed=embed)
    except Exception as e:
        await ctx.respond(f"❌ Ban işlemi başarısız: {e}", ephemeral=True)


# ══════════════════════════════════════════════════════════════════
#  /kick
# ══════════════════════════════════════════════════════════════════
@bot.slash_command(name="kick", description="👢 Belirtilen kullanıcıyı sunucudan atar.")
@commands.has_permissions(kick_members=True)
@option("kullanıcı", discord.Member, description="Kicklenecek kullanıcıyı seçin.")
@option("sebep", str, description="Atma sebebini girin.", required=False, default="Sebep belirtilmedi.")
async def kick(ctx: discord.ApplicationContext, kullanıcı: discord.Member, sebep: str):
    try:
        await kullanıcı.kick(reason=f"{ctx.author} tarafından: {sebep}")
        embed = discord.Embed(title="👢  Kullanıcı Atıldı", color=discord.Color.orange())
        embed.set_author(name="Project Nova • Moderasyon")
        embed.add_field(name="👤 Kullanıcı",  value=f"{kullanıcı} ({kullanıcı.id})", inline=True)
        embed.add_field(name="🛡️ Moderatör", value=str(ctx.author),                 inline=True)
        embed.add_field(name="📋 Sebep",       value=sebep,                           inline=False)
        embed.add_field(name="📅 Tarih",       value=discord.utils.format_dt(discord.utils.utcnow(), "F"), inline=False)
        embed.set_thumbnail(url=kullanıcı.display_avatar.url)
        embed.set_footer(text="Project Nova • Moderasyon Sistemi")
        embed.timestamp = discord.utils.utcnow()
        await ctx.respond(embed=embed)
    except Exception as e:
        await ctx.respond(f"❌ Kick işlemi başarısız: {e}", ephemeral=True)


# ══════════════════════════════════════════════════════════════════
#  /mute
# ══════════════════════════════════════════════════════════════════
@bot.slash_command(name="mute", description="🔇 Belirtilen kullanıcıyı susturur. Süre dakika cinsinden girilir.")
@commands.has_permissions(moderate_members=True)
@option("kullanıcı", discord.Member, description="Susturulacak kullanıcıyı seçin.")
@option("süre",      int,            description="Susturma süresi (dakika, maks 40320 = 28 gün).", min_value=1, max_value=40320)
@option("sebep",     str,            description="Susturma sebebini girin.", required=False, default="Sebep belirtilmedi.")
async def mute(ctx: discord.ApplicationContext, kullanıcı: discord.Member, süre: int, sebep: str):
    import datetime
    duration = datetime.timedelta(minutes=süre)
    try:
        await kullanıcı.timeout_for(duration, reason=f"{ctx.author} tarafından: {sebep}")

        if süre >= 60:
            time_str = f"{süre // 60} saat {süre % 60} dakika"
        else:
            time_str = f"{süre} dakika"

        end_ts = discord.utils.utcnow() + duration

        embed = discord.Embed(title="🔇  Kullanıcı Susturuldu", color=discord.Color.purple())
        embed.set_author(name="Project Nova • Moderasyon")
        embed.add_field(name="👤 Kullanıcı",    value=f"{kullanıcı} ({kullanıcı.id})",       inline=True)
        embed.add_field(name="🛡️ Moderatör",   value=str(ctx.author),                        inline=True)
        embed.add_field(name="⏱️ Süre",         value=time_str,                               inline=True)
        embed.add_field(name="📋 Sebep",         value=sebep,                                  inline=False)
        embed.add_field(name="📅 Bitiş Tarihi", value=discord.utils.format_dt(end_ts, "F"),  inline=False)
        embed.set_thumbnail(url=kullanıcı.display_avatar.url)
        embed.set_footer(text="Project Nova • Moderasyon Sistemi")
        embed.timestamp = discord.utils.utcnow()
        await ctx.respond(embed=embed)
    except Exception as e:
        await ctx.respond(f"❌ Mute işlemi başarısız: {e}", ephemeral=True)


# ══════════════════════════════════════════════════════════════════
#  /uye-sayisi
# ══════════════════════════════════════════════════════════════════
@bot.slash_command(name="uye-sayisi", description="👥 Sunucunun güncel üye sayısını gösterir.")
async def uye_sayisi(ctx: discord.ApplicationContext):
    guild = ctx.guild
    online = sum(
        1 for m in guild.members
        if m.status != discord.Status.offline and not m.bot
    )
    embed = discord.Embed(
        title="👥  Sunucu İstatistikleri",
        description=f"**{guild.name}** sunucusunun güncel üye bilgileri:",
        color=discord.Color.blue(),
    )
    embed.set_author(name="Project Nova")
    embed.add_field(name="📊 Toplam Üye",      value=f"**{guild.member_count}** kişi",                                    inline=True)
    embed.add_field(name="🟢 Çevrimiçi",       value=f"**{online}** kişi",                                                inline=True)
    embed.add_field(name="📅 Sunucu Kuruluş",  value=discord.utils.format_dt(guild.created_at, "D"),                     inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="Project Nova • İstatistik Sistemi")
    embed.timestamp = discord.utils.utcnow()
    await ctx.respond(embed=embed)


# ══════════════════════════════════════════════════════════════════
#  /partner-basvuru  — Modal
# ══════════════════════════════════════════════════════════════════
class PartnerModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="🤝 Partnerlik Başvurusu — Project Nova")
        self.add_item(discord.ui.InputText(
            label="Sunucunuz Kaç Kişi?",
            placeholder="Örnek: 1500 üye",
            max_length=20,
        ))
        self.add_item(discord.ui.InputText(
            label="Everyone Limiti (Everyone/Everyonesiz)",
            placeholder="Everyone var mı, yok mu?",
            max_length=50,
        ))
        self.add_item(discord.ui.InputText(
            label="Partnerlik Yapmak İstiyorsunuz",
            placeholder="Reklam partneri, içerik partneri vb.",
            max_length=100,
        ))
        self.add_item(discord.ui.InputText(
            label="Neden Biz?",
            placeholder="Neden Project Nova ile partner olmak istiyorsunuz?",
            style=discord.InputTextStyle.long,
            max_length=500,
        ))

    async def callback(self, interaction: discord.Interaction):
        member_count = self.children[0].value
        everyone     = self.children[1].value
        p_type       = self.children[2].value
        why_us       = self.children[3].value
        user         = interaction.user

        embed = discord.Embed(
            title="🤝  Partnerlik Başvurusu Alındı",
            description=f"**{user}** bir partnerlik başvurusu gönderdi.",
            color=discord.Color.blue(),
        )
        embed.set_author(name="Yeni Partnerlik Başvurusu")
        embed.add_field(name="👤 Başvuran",             value=f"{user.mention} ({user})",    inline=True)
        embed.add_field(name="🆔 Kullanıcı ID",         value=str(user.id),                  inline=True)
        embed.add_field(name="👥 Sunucu Üye Sayısı",    value=member_count,                  inline=True)
        embed.add_field(name="📢 Everyone Durumu",      value=everyone,                      inline=True)
        embed.add_field(name="🤝 Partner Türü",         value=p_type,                        inline=False)
        embed.add_field(name="💬 Neden Biz?",           value=why_us,                        inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="Project Nova • Partnerlik Sistemi")
        embed.timestamp = discord.utils.utcnow()

        accept_btn = discord.ui.Button(label="✅ Onayla", style=discord.ButtonStyle.success, custom_id=f"partner_accept_{user.id}")
        reject_btn = discord.ui.Button(label="❌ Reddet", style=discord.ButtonStyle.danger,  custom_id=f"partner_reject_{user.id}")

        async def accept_cb(i: discord.Interaction):
            await i.response.send_message(f"✅ {user.mention} için partnerlik başvurusu **onaylandı**.", ephemeral=True)

        async def reject_cb(i: discord.Interaction):
            await i.response.send_message(f"❌ {user.mention} için partnerlik başvurusu **reddedildi**.", ephemeral=True)

        accept_btn.callback = accept_cb
        reject_btn.callback = reject_cb
        action_view = discord.ui.View(timeout=None)
        action_view.add_item(accept_btn)
        action_view.add_item(reject_btn)

        ch = bot.get_channel(PARTNER_CH_ID)
        if ch:
            await ch.send(embed=embed, view=action_view)

        await interaction.response.send_message(
            embed=nova_embed(
                "✅ Başvuru Alındı!",
                "Partnerlik başvurunuz başarıyla alındı! Ekibimiz inceleyecek ve en kısa sürede geri dönüş yapacaktır.\n\n"
                "⏱️ İnceleme süresi genellikle **24-48 saat** arasındadır.",
                discord.Color.green(),
            ),
            ephemeral=True,
        )


@bot.slash_command(name="partner-basvuru", description="🤝 Partnerlik başvurusu yapmak için formu açar.")
async def partner_basvuru(ctx: discord.ApplicationContext):
    if ctx.channel_id != PARTNER_CH_ID:
        await ctx.respond(
            embed=nova_embed(
                "❌ Yanlış Kanal",
                f"Bu komut yalnızca <#{PARTNER_CH_ID}> kanalında kullanılabilir!",
                discord.Color.red(),
            ),
            ephemeral=True,
        )
        return
    await ctx.send_modal(PartnerModal())


# ══════════════════════════════════════════════════════════════════
#  /istekleriniz  — Modal
# ══════════════════════════════════════════════════════════════════
class RequestModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="💡 İstek & Öneri — Project Nova")
        self.add_item(discord.ui.InputText(
            label="İsteğinizi Belirtin",
            placeholder="Sunucumuz veya botumuz için bir öneriniz var mı? Lütfen detaylı açıklayın...",
            style=discord.InputTextStyle.long,
            min_length=10,
            max_length=1000,
        ))

    async def callback(self, interaction: discord.Interaction):
        text = self.children[0].value
        user = interaction.user

        embed = discord.Embed(
            title="💡  Yeni İstek Alındı",
            description=text,
            color=discord.Color.purple(),
        )
        embed.set_author(name="Yeni İstek & Öneri")
        embed.add_field(name="👤 Gönderen",  value=f"{user.mention} ({user})", inline=True)
        embed.add_field(name="🆔 ID",        value=str(user.id),               inline=True)
        embed.add_field(name="📅 Tarih",     value=discord.utils.format_dt(discord.utils.utcnow(), "F"), inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="Project Nova • İstek Sistemi")
        embed.timestamp = discord.utils.utcnow()

        ch = bot.get_channel(REQUEST_CH_ID)
        if ch:
            await ch.send(embed=embed)

        await interaction.response.send_message(
            embed=nova_embed(
                "✅ İstek Gönderildi!",
                "İsteğiniz başarıyla iletildi! Ekibimiz inceleyecek ve değerlendireceğiz.\n\n"
                "Geri bildiriminiz için teşekkür ederiz! 🙏",
                discord.Color.green(),
            ),
            ephemeral=True,
        )


@bot.slash_command(name="istekleriniz", description="💡 İstek veya öneri göndermek için formu açar.")
async def istekleriniz(ctx: discord.ApplicationContext):
    if ctx.channel_id != REQUEST_CH_ID:
        await ctx.respond(
            embed=nova_embed(
                "❌ Yanlış Kanal",
                f"Bu komut yalnızca <#{REQUEST_CH_ID}> kanalında kullanılabilir!",
                discord.Color.red(),
            ),
            ephemeral=True,
        )
        return
    await ctx.send_modal(RequestModal())


# ══════════════════════════════════════════════════════════════════
#  HATA YÖNETİMİ
# ══════════════════════════════════════════════════════════════════
@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond(
            embed=nova_embed("❌ Yetersiz Yetki", "Bu komutu kullanmak için gerekli yetkiye sahip değilsin.", discord.Color.red()),
            ephemeral=True,
        )
    else:
        await ctx.respond(f"❌ Bir hata oluştu: {error}", ephemeral=True)
        raise error


# ══════════════════════════════════════════════════════════════════
#  BAŞLAT
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    bot.run(TOKEN)
