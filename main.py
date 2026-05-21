import os
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import asyncio
import re
from datetime import timedelta

TOKEN = os.getenv("TOKEN")
 
VERIFIED_ROLE_ID     = 1482031063936139264   # Doğrulama rolü (yeşil tik)
ANNOUNCEMENT_CH_ID   = 1482021925319344409   # /duyuru-paylas hedef kanalı
PARTNER_CH_ID        = 1482021699020132486   # /partner-basvuru sadece bu kanal
REQUEST_CH_ID        = 1482034060678140015   # /istekleriniz sadece bu kanal
 
COLOR_PRIMARY  = 0x7B2FBE
COLOR_SUCCESS  = 0x2ECC71
COLOR_ERROR    = 0xE74C3C
COLOR_WARNING  = 0xF39C12
COLOR_INFO     = 0x3498DB
COLOR_TICKET   = 0x5865F2
 
# Küfür listesi — istediğiniz kelimeleri ekleyin
BANNED_WORDS = [
    "küfür1", "küfür2", "küfür3",
]
 
open_tickets: dict = {}  # user_id -> channel_id
 
# ═══════════════════════════════════════════════════════════════
#                     BOT KURULUMU
# ═══════════════════════════════════════════════════════════════
 
intents = nextcord.Intents.default()
intents.message_content = True
intents.members          = True
 
bot = commands.Bot(command_prefix="!", intents=intents)
 
# ═══════════════════════════════════════════════════════════════
#                       YARDIMCI
# ═══════════════════════════════════════════════════════════════
 
def nova_embed(title, description="", color=COLOR_PRIMARY):
    e = nextcord.Embed(title=title, description=description, color=color)
    e.set_footer(text="✦ Project Nova")
    return e
 
def contains_banned_word(text):
    lowered = text.lower()
    for word in BANNED_WORDS:
        if re.search(rf"\b{re.escape(word.lower())}\b", lowered):
            return True
    return False
 
async def is_admin(interaction):
    return interaction.user.guild_permissions.administrator
 
async def check_channel(interaction, allowed_id):
    if interaction.channel_id != allowed_id:
        ch = interaction.guild.get_channel(allowed_id)
        mention = ch.mention if ch else f"<#{allowed_id}>"
        await interaction.response.send_message(
            embed=nova_embed("❌  Yanlış Kanal",
                f"Bu komutu yalnızca {mention} kanalında kullanabilirsiniz.", COLOR_ERROR),
            ephemeral=True,
        )
        return False
    return True
 
# ═══════════════════════════════════════════════════════════════
#                         OLAYLAR
# ═══════════════════════════════════════════════════════════════
 
@bot.event
async def on_ready():
    print(f"✅  {bot.user} olarak giriş yapıldı!")
    total = sum(g.member_count for g in bot.guilds)
    await bot.change_presence(
        activity=nextcord.Activity(type=nextcord.ActivityType.watching,
            name=f"{total} Üye ile Büyüyoruz 🚀")
    )
 
@bot.event
async def on_member_join(member):
    total = sum(g.member_count for g in bot.guilds)
    await bot.change_presence(
        activity=nextcord.Activity(type=nextcord.ActivityType.watching,
            name=f"{total} Üye ile Büyüyoruz 🚀")
    )
 
@bot.event
async def on_member_remove(member):
    total = sum(g.member_count for g in bot.guilds)
    await bot.change_presence(
        activity=nextcord.Activity(type=nextcord.ActivityType.watching,
            name=f"{total} Üye ile Büyüyoruz 🚀")
    )
 
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if contains_banned_word(message.content):
        try:
            await message.delete()
        except Exception:
            pass
        warn = await message.channel.send(
            embed=nova_embed("🚫  Uygunsuz İçerik",
                f"{message.author.mention}, uygunsuz kelime kullanımı nedeniyle "
                f"mesajın silindi. Lütfen sunucu kurallarına uy!\n\n"
                f"Tekrar eden ihlaller ceza ile sonuçlanacaktır.", COLOR_ERROR)
        )
        await asyncio.sleep(5)
        try:
            await warn.delete()
        except Exception:
            pass
    await bot.process_commands(message)
 
# ═══════════════════════════════════════════════════════════════
#               TİCKET SİSTEMİ — /ticket-kur
# ═══════════════════════════════════════════════════════════════
 
class TicketCategorySelect(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(label="Sipariş",            description="Yeni bir sipariş vermek istiyorum",              emoji="⭐", value="siparis"),
            nextcord.SelectOption(label="Destek",             description="Bir sorunum var, yardım istiyorum",              emoji="💫", value="destek"),
            nextcord.SelectOption(label="Proje İsteği",       description="Özel proje talebi oluşturmak istiyorum",        emoji="🌟", value="proje_istegi"),
            nextcord.SelectOption(label="Ücretsiz Proje Alma",description="Ücretsiz proje hakkında bilgi almak istiyorum", emoji="✨", value="ucretsiz_proje"),
            nextcord.SelectOption(label="Diğer",              description="Diğer konular hakkında",                        emoji="💠", value="diger"),
        ]
        super().__init__(placeholder="📂  Bir kategori seç...", min_values=1, max_values=1,
                         options=options, custom_id="ticket_category_select")
 
    async def callback(self, interaction: Interaction):
        guild  = interaction.guild
        user   = interaction.user
        choice = self.values[0]
        labels = {
            "siparis":        ("Sipariş",              "⭐"),
            "destek":         ("Destek",               "💫"),
            "proje_istegi":   ("Proje İsteği",         "🌟"),
            "ucretsiz_proje": ("Ücretsiz Proje Alma",  "✨"),
            "diger":          ("Diğer",                "💠"),
        }
        label, emoji = labels.get(choice, ("Ticket", "🎫"))
 
        if user.id in open_tickets:
            existing = guild.get_channel(open_tickets[user.id])
            if existing:
                await interaction.response.send_message(
                    embed=nova_embed("⚠️  Mevcut Ticket",
                        f"Zaten açık bir ticket'ın var: {existing.mention}\nÖnce mevcut ticket'ını kapat.",
                        COLOR_WARNING), ephemeral=True)
                return
 
        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
            user: nextcord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: nextcord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        ticket_ch = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            topic=f"{emoji} {label} | {user} tarafından açıldı",
        )
        open_tickets[user.id] = ticket_ch.id
 
        close_view = CloseTicketView()
        ticket_embed = nextcord.Embed(
            title=f"{emoji}  {label} — Ticket Açıldı",
            description=(
                f"Merhaba {user.mention}! 👋\n\n"
                f"**Kategori:** {emoji} {label}\n\n"
                f"**📋 Talebini detaylıca açıklaman yeterli**, ekibimiz en kısa sürede sana yardımcı olacak.\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🕒 Ortalama yanıt süresi: **5–30 dakika**\n"
                f"📌 Lütfen konu dışı mesaj atmaktan kaçının.\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Ticket'ı kapatmak için aşağıdaki butona basın."
            ),
            color=COLOR_TICKET,
        )
        ticket_embed.set_footer(text="✦ Project Nova — Destek Merkezi")
        await ticket_ch.send(embed=ticket_embed, view=close_view)
        await interaction.response.send_message(
            embed=nova_embed("✅  Ticket Oluşturuldu",
                f"Ticket kanalın hazır: {ticket_ch.mention}\nBir yetkili en kısa sürede ilgilenecek!",
                COLOR_SUCCESS), ephemeral=True)
 
 
class CloseTicketView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @nextcord.ui.button(label="🔒  Ticket'ı Kapat", style=nextcord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, button, interaction: Interaction):
        channel  = interaction.channel
        owner_id = next((uid for uid, cid in open_tickets.items() if cid == channel.id), None)
        if owner_id:
            open_tickets.pop(owner_id, None)
        await channel.send(embed=nova_embed("🔒  Ticket Kapatıldı",
            f"Bu ticket {interaction.user.mention} tarafından kapatıldı.\nKanal **5 saniye** içinde silinecek.",
            COLOR_ERROR))
        await asyncio.sleep(5)
        try:
            await channel.delete(reason="Ticket kapatıldı")
        except Exception:
            pass
 
 
class TicketPanelView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())
 
 
@bot.slash_command(name="ticket-kur", description="🎫 Destek Merkezi panelini gönderir. (Admin)")
async def ticket_kur(interaction: Interaction):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR), ephemeral=True)
    embed = nextcord.Embed(
        title="🎫  Destek Merkezi",
        description=(
            "**💜  Destek Merkezi Hakkında.**\n"
            "Aşağıdaki seçeneklerden uygun olanı seçerek hemen bir ticket oluşturabilirsiniz.\n\n"
            "**📌  Sunucu Bilgisi.**\n"
            "Gereksiz ticket açmayın, Sunucu Kurallarını Okumayı Unutmayın.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⭐  **Sipariş** — Yeni bir sipariş vermek istiyorum\n"
            "💫  **Destek** — Bir sorunum var, yardım istiyorum\n"
            "🌟  **Proje İsteği** — Özel proje talebi oluşturmak istiyorum\n"
            "✨  **Ücretsiz Proje Alma** — Ücretsiz proje hakkında bilgi almak istiyorum\n"
            "💠  **Diğer** — Diğer konular hakkında\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_TICKET,
    )
    embed.set_footer(text="✦ Project Nova — Destek Merkezi")
    await interaction.channel.send(embed=embed, view=TicketPanelView())
    await interaction.response.send_message(
        embed=nova_embed("✅ Panel Gönderildi", "Ticket paneli başarıyla gönderildi!", COLOR_SUCCESS), ephemeral=True)
 
# ═══════════════════════════════════════════════════════════════
#            DOĞRULAMA — /dogrulama
# ═══════════════════════════════════════════════════════════════
 
class VerifyView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
 
    @nextcord.ui.button(label="✅  Doğrula — Sunucuya Katıl", style=nextcord.ButtonStyle.success, custom_id="verify_btn")
    async def verify(self, button, interaction: Interaction):
        role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        if role is None:
            return await interaction.response.send_message(
                embed=nova_embed("⚠️  Hata", "Doğrulama rolü bulunamadı. Yetkili ile iletişime geçin.", COLOR_WARNING),
                ephemeral=True)
        if role in interaction.user.roles:
            return await interaction.response.send_message(
                embed=nova_embed("ℹ️  Zaten Doğrulandın", "Zaten doğrulanmışsın! Sunucunun tadını çıkar 🎉", COLOR_INFO),
                ephemeral=True)
        await interaction.user.add_roles(role, reason="Doğrulama butonu")
        await interaction.response.send_message(
            embed=nova_embed("🎉  Hoş Geldin!",
                f"{interaction.user.mention} **Project Nova**'ya hoş geldin!\n\n"
                f"✅ Doğrulandın ve tüm kanallara erişim kazandın.\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 Kuralları oku ve eğlenceli zaman geçir! 🚀",
                COLOR_SUCCESS), ephemeral=True)
 
 
@bot.slash_command(name="dogrulama", description="✅ Doğrulama panelini gönderir. (Admin)")
async def dogrulama(interaction: Interaction):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR), ephemeral=True)
    embed = nextcord.Embed(
        title="🔐  Sunucu Doğrulama Sistemi",
        description=(
            "**Project Nova'ya Hoş Geldin!** 🎉\n\n"
            "Sunucumuza tam erişim kazanmak için aşağıdaki **Doğrula** butonuna basman yeterli.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅  Butona bastıktan sonra tüm kanallara erişim kazanacaksın.\n"
            "📌  Lütfen kuralları oku ve eğlenceli zaman geçir!\n"
            "🚀  Umarız aramızda keyifli zaman geçirirsin.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_PRIMARY,
    )
    embed.set_footer(text="✦ Project Nova — Doğrulama Sistemi")
    await interaction.channel.send(embed=embed, view=VerifyView())
    await interaction.response.send_message(
        embed=nova_embed("✅ Panel Gönderildi", "Doğrulama paneli başarıyla gönderildi!", COLOR_SUCCESS), ephemeral=True)
 
# ═══════════════════════════════════════════════════════════════
#             DUYURU — /duyuru-paylas
# ═══════════════════════════════════════════════════════════════
 
@bot.slash_command(name="duyuru-paylas", description="📢 Duyuru kanalına mesaj gönderir. (Admin)")
async def duyuru_paylas(interaction: Interaction,
    mesaj: str = SlashOption(name="mesaj", description="Duyuru metni", required=True)):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR), ephemeral=True)
    ch = interaction.guild.get_channel(ANNOUNCEMENT_CH_ID)
    if ch is None:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Hata", "Duyuru kanalı bulunamadı.", COLOR_ERROR), ephemeral=True)
    embed = nextcord.Embed(title="📢  Yeni Duyuru", description=mesaj, color=COLOR_PRIMARY)
    embed.set_author(name=f"{interaction.user.display_name} tarafından", icon_url=interaction.user.display_avatar.url)
    embed.set_footer(text="✦ Project Nova — Duyuru")
    await ch.send("@everyone", embed=embed)
    await interaction.response.send_message(
        embed=nova_embed("✅ Duyuru Gönderildi", f"Duyurun {ch.mention} kanalına gönderildi!", COLOR_SUCCESS), ephemeral=True)
 
# ═══════════════════════════════════════════════════════════════
#          PARTNER BAŞVURU — /partner-basvuru
# ═══════════════════════════════════════════════════════════════
 
class PartnerModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title="🤝  Partner Başvuru Formu")
        self.uye_sayisi = nextcord.ui.TextInput(
            label="Sunucunuz Kaç Kişi?", placeholder="Örn: 500", max_length=10)
        self.everyone_limit = nextcord.ui.TextInput(
            label="Everyone Limiti (Everyone mi / Everyonesiz mi?)",
            placeholder="Örn: Everyone var / Everyone yok", max_length=50)
        self.neden_biz = nextcord.ui.TextInput(
            label="Neden Biz? (Neden Partnerlik İstiyorsunuz?)",
            placeholder="Partnerlik yapmak istemenizin sebebini yazın...",
            style=nextcord.TextInputStyle.paragraph, max_length=500)
        self.add_item(self.uye_sayisi)
        self.add_item(self.everyone_limit)
        self.add_item(self.neden_biz)
 
    async def callback(self, interaction: Interaction):
        embed = nextcord.Embed(
            title="🤝  Yeni Partner Başvurusu",
            description=(
                f"**Başvuran:** {interaction.user.mention} (`{interaction.user}`)\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👥  **Üye Sayısı:** {self.uye_sayisi.value}\n\n"
                f"📢  **Everyone Limiti:** {self.everyone_limit.value}\n\n"
                f"💬  **Neden Biz:**\n{self.neden_biz.value}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=COLOR_PRIMARY,
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="✦ Project Nova — Partner Başvuru")
        partner_ch = interaction.guild.get_channel(PARTNER_CH_ID)
        if partner_ch:
            await partner_ch.send(embed=embed)
        await interaction.response.send_message(
            embed=nova_embed("✅  Başvurunuz Alındı!",
                "Partner başvurunuz başarıyla gönderildi! ✅\n"
                "Ekibimiz en kısa sürede değerlendirerek size dönüş yapacak. 🤝",
                COLOR_SUCCESS), ephemeral=True)
 
 
@bot.slash_command(name="partner-basvuru", description="🤝 Partner başvuru formunu açar.")
async def partner_basvuru(interaction: Interaction):
    if not await check_channel(interaction, PARTNER_CH_ID):
        return
    await interaction.response.send_modal(PartnerModal())
 
# ═══════════════════════════════════════════════════════════════
#              İSTEKLER — /istekleriniz
# ═══════════════════════════════════════════════════════════════
 
class RequestModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title="💡  İstek / Öneri Formu")
        self.istek = nextcord.ui.TextInput(
            label="İsteğinizi Belirtin",
            placeholder="Sunucumuz veya botumuz için istek/öneri yazın...",
            style=nextcord.TextInputStyle.paragraph, max_length=1000)
        self.add_item(self.istek)
 
    async def callback(self, interaction: Interaction):
        embed = nextcord.Embed(
            title="💡  Yeni İstek / Öneri",
            description=(
                f"**Gönderen:** {interaction.user.mention} (`{interaction.user}`)\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📝  **İstek/Öneri:**\n{self.istek.value}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=COLOR_INFO,
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="✦ Project Nova — İstek Sistemi")
        req_ch = interaction.guild.get_channel(REQUEST_CH_ID)
        if req_ch:
            msg = await req_ch.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
        await interaction.response.send_message(
            embed=nova_embed("✅  İsteğiniz Alındı!",
                "İsteğiniz başarıyla iletildi! 💡\nEkibimiz en kısa sürede inceleyecek. 🙏",
                COLOR_SUCCESS), ephemeral=True)
 
 
@bot.slash_command(name="istekleriniz", description="💡 İstek ve öneri formunu açar.")
async def istekleriniz(interaction: Interaction):
    if not await check_channel(interaction, REQUEST_CH_ID):
        return
    await interaction.response.send_modal(RequestModal())
 
# ═══════════════════════════════════════════════════════════════
#            MODERASYON — ban / kick / mute
# ═══════════════════════════════════════════════════════════════
 
@bot.slash_command(name="ban", description="🔨 Belirtilen üyeyi sunucudan yasaklar. (Moderatör)")
async def ban(interaction: Interaction,
    uye: nextcord.Member = SlashOption(name="uye", description="Yasaklanacak üye", required=True),
    sebep: str = SlashOption(name="sebep", description="Yasaklama sebebi", required=False, default="Sebep belirtilmedi"),
    mesaj_silme: int = SlashOption(name="mesaj_silme", description="Kaç günlük mesaj silinsin? (0-7)",
        required=False, default=0, min_value=0, max_value=7)):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok.", COLOR_ERROR), ephemeral=True)
    if uye.top_role >= interaction.user.top_role:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Hata", "Kendinizden üst/eşit roldekini yasaklayamazsınız!", COLOR_ERROR), ephemeral=True)
    try:
        await uye.send(embed=nova_embed("🔨  Yasaklandınız",
            f"**{interaction.guild.name}** sunucusundan yasaklandınız.\n\n"
            f"**Sebep:** {sebep}\n**Yetkili:** {interaction.user}", COLOR_ERROR))
    except Exception:
        pass
    await uye.ban(reason=f"{interaction.user}: {sebep}", delete_message_days=mesaj_silme)
    embed = nextcord.Embed(title="🔨  Üye Yasaklandı",
        description=(f"**Yasaklanan:** {uye.mention} (`{uye}`)\n**Yetkili:** {interaction.user.mention}\n"
            f"**Sebep:** {sebep}\n**Silinen Mesaj:** Son {mesaj_silme} gün\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nBu işlem kalıcıdır."), color=COLOR_ERROR)
    embed.set_thumbnail(url=uye.display_avatar.url)
    embed.set_footer(text="✦ Project Nova — Moderasyon")
    await interaction.response.send_message(embed=embed)
 
 
@bot.slash_command(name="kick", description="👢 Belirtilen üyeyi sunucudan atar. (Moderatör)")
async def kick(interaction: Interaction,
    uye: nextcord.Member = SlashOption(name="uye", description="Atılacak üye", required=True),
    sebep: str = SlashOption(name="sebep", description="Atma sebebi", required=False, default="Sebep belirtilmedi")):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok.", COLOR_ERROR), ephemeral=True)
    if uye.top_role >= interaction.user.top_role:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Hata", "Kendinizden üst/eşit roldekini atamazsınız!", COLOR_ERROR), ephemeral=True)
    try:
        await uye.send(embed=nova_embed("👢  Atıldınız",
            f"**{interaction.guild.name}** sunucusundan atıldınız.\n\n"
            f"**Sebep:** {sebep}\n**Yetkili:** {interaction.user}", COLOR_WARNING))
    except Exception:
        pass
    await uye.kick(reason=f"{interaction.user}: {sebep}")
    embed = nextcord.Embed(title="👢  Üye Atıldı",
        description=(f"**Atılan:** {uye.mention} (`{uye}`)\n**Yetkili:** {interaction.user.mention}\n"
            f"**Sebep:** {sebep}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nÜye tekrar katılabilir."),
        color=COLOR_WARNING)
    embed.set_thumbnail(url=uye.display_avatar.url)
    embed.set_footer(text="✦ Project Nova — Moderasyon")
    await interaction.response.send_message(embed=embed)
 
 
@bot.slash_command(name="mute", description="🔇 Belirtilen üyeyi susturur. (Moderatör)")
async def mute(interaction: Interaction,
    uye: nextcord.Member = SlashOption(name="uye", description="Susturulacak üye", required=True),
    sure: int = SlashOption(name="sure", description="Süre (dakika) — 0 = kalıcı (28 gün)", required=False, default=0, min_value=0, max_value=40320),
    sebep: str = SlashOption(name="sebep", description="Susturma sebebi", required=False, default="Sebep belirtilmedi")):
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok.", COLOR_ERROR), ephemeral=True)
    if uye.top_role >= interaction.user.top_role:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Hata", "Kendinizden üst/eşit roldekini susturamazsınız!", COLOR_ERROR), ephemeral=True)
    sure_str = f"{sure} dakika" if sure > 0 else "Kalıcı (28 gün)"
    delta = timedelta(minutes=sure) if sure > 0 else timedelta(days=28)
    await uye.edit(timeout=nextcord.utils.utcnow() + delta, reason=f"{interaction.user}: {sebep}")
    try:
        await uye.send(embed=nova_embed("🔇  Susturuldunuz",
            f"**{interaction.guild.name}** sunucusunda susturuldunuz.\n\n"
            f"**Sebep:** {sebep}\n**Süre:** {sure_str}\n**Yetkili:** {interaction.user}", COLOR_WARNING))
    except Exception:
        pass
    embed = nextcord.Embed(title="🔇  Üye Susturuldu",
        description=(f"**Susturulan:** {uye.mention} (`{uye}`)\n**Yetkili:** {interaction.user.mention}\n"
            f"**Sebep:** {sebep}\n**Süre:** {sure_str}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nSüre dolunca otomatik açılır."),
        color=COLOR_WARNING)
    embed.set_thumbnail(url=uye.display_avatar.url)
    embed.set_footer(text="✦ Project Nova — Moderasyon")
    await interaction.response.send_message(embed=embed)
 
 
@bot.slash_command(name="unmute", description="🔊 Üyenin susturmasını kaldırır. (Moderatör)")
async def unmute(interaction: Interaction,
    uye: nextcord.Member = SlashOption(name="uye", description="Susturması kaldırılacak üye", required=True)):
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok.", COLOR_ERROR), ephemeral=True)
    await uye.edit(timeout=None)
    await interaction.response.send_message(
        embed=nova_embed("🔊  Susturma Kaldırıldı",
            f"**Üye:** {uye.mention}\n**Yetkili:** {interaction.user.mention}", COLOR_SUCCESS))
 
 
@bot.slash_command(name="unban", description="🔓 Yasaklı üyenin yasağını kaldırır. (Moderatör)")
async def unban(interaction: Interaction,
    kullanici_id: str = SlashOption(name="kullanici_id", description="Kullanıcı ID'si", required=True),
    sebep: str = SlashOption(name="sebep", description="Sebep", required=False, default="Sebep belirtilmedi")):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok.", COLOR_ERROR), ephemeral=True)
    try:
        user = await bot.fetch_user(int(kullanici_id))
        await interaction.guild.unban(user, reason=f"{interaction.user}: {sebep}")
        await interaction.response.send_message(
            embed=nova_embed("🔓  Yasak Kaldırıldı",
                f"**Kullanıcı:** {user} (`{user.id}`)\n**Yetkili:** {interaction.user.mention}\n**Sebep:** {sebep}",
                COLOR_SUCCESS))
    except Exception as e:
        await interaction.response.send_message(
            embed=nova_embed("❌ Hata", f"Yasak kaldırılamadı: {e}", COLOR_ERROR), ephemeral=True)
 
# ═══════════════════════════════════════════════════════════════
#            ÜYE SAYISI — /uyesayisi
# ═══════════════════════════════════════════════════════════════
 
@bot.slash_command(name="uyesayisi", description="📊 Sunucunun üye sayısını gösterir.")
async def uyesayisi(interaction: Interaction):
    guild  = interaction.guild
    total  = guild.member_count
    bots   = sum(1 for m in guild.members if m.bot)
    humans = total - bots
    embed  = nextcord.Embed(
        title="📊  Sunucu İstatistikleri",
        description=(
            f"**{guild.name}** sunucusunun güncel üye istatistikleri:\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥  **Toplam Üye:** `{total:,}`\n"
            f"🧑  **İnsan Üye:** `{humans:,}`\n"
            f"🤖  **Bot:** `{bots:,}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 **Project Nova ile Büyümeye Devam Ediyoruz!**"
        ),
        color=COLOR_PRIMARY,
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="✦ Project Nova — İstatistik")
    await interaction.response.send_message(embed=embed)
 
# ═══════════════════════════════════════════════════════════════
#                        BAŞLAT
# ═══════════════════════════════════════════════════════════════
 
bot.run(TOKEN)
