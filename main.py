import os
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import asyncio
import re
from datetime import timedelta
from collections import defaultdict

TOKEN = os.getenv("TOKEN")

# ── ID'ler ─────────────────────────────────────────────────────
VERIFIED_ROLE_ID       = 1482031063936139264
AUTO_ROLE_ID           = 1482031140897292563
ANNOUNCEMENT_CH_ID     = 1482021925319344409
PARTNER_CH_ID          = 1482021699020132486
REQUEST_CH_ID          = 1482034060678140015
EMBED_RELAY_CH_ID      = 1483112387199504474
TICKET_LOG_CH_ID       = 1506945404569255967
TICKET_CATEGORY_ID     = 1506935742847254568
OZEL_PROJE_CATEGORY_ID = 1506947665940709376
ONCELIKLI_CATEGORY_ID  = 1506948002525352066

# ── Renkler ────────────────────────────────────────────────────
COLOR_PRIMARY  = 0x7B2FBE
COLOR_SUCCESS  = 0x2ECC71
COLOR_ERROR    = 0xE74C3C
COLOR_WARNING  = 0xF39C12
COLOR_INFO     = 0x3498DB
COLOR_TICKET   = 0x5865F2

# ═══════════════════════════════════════════════════════════════
#          GELİŞMİŞ KÜFÜR / YASAK KELİME LİSTESİ
# ═══════════════════════════════════════════════════════════════

BANNED_WORDS = [
    # ── Türkçe Küfür Kısaltmaları & Argo ────────────────────────
    "amk", "sg", "oç", "mk", "ylo", "bok",
    "orospu çocuğu", "oc", "o.c", "o.ç",
    "s.g", "s*g", "amq", "a.m.k", "a.m.q",
    "sktr", "sktir", "sktir git", "stg", "stfu",
    "wtf", "wth", "kys", "gtfo",

    # ── Türkçe Küfür (doğrudan & varyant) ──────────────────────
    "amına", "amını", "amın", "boktan", "boklu",
    "orospu", "orospuçocuğu", "orospunun", "piç", "piçlik",
    "göt", "götü", "götveren", "sik", "sikin", "sikik", "sikiş",
    "sikeyim", "siktir", "siktirin", "sikerim", "siktirgit",
    "yarrak", "yarrağı", "yarak", "yaraklar", "çük",
    "ibne", "ibnelik", "pezeveng", "pezevenk",
    "kahpe", "kahpeler", "kaltak", "şerefsiz", "şerefsizlik",
    "haysiyetsiz", "namussuz", "namussuzu", "gerizekalı",
    "geri zekalı", "salak", "aptal", "mal", "dangalak",
    "sürtük", "fahişe",

    # ── İngilizce Küfür & Kısaltmaları ──────────────────────────
    "bitch", "btch", "b1tch", "b!tch",
    "whore", "wh0re",
    "fuck", "fck", "f*ck", "f.uck", "fucker", "fucking", "fuk",
    "shit", "sh!t", "sh1t", "sht",
    "asshole", "a**hole", "a55hole",
    "pussy", "p*ssy", "p.ussy",
    "dick", "d1ck", "d*ck",
    "cock", "c0ck",
    "bastard", "b4stard",
    "motherfucker", "mf", "mofo",
    "cunt", "c*nt",
    "nigga", "nigger", "n1gga", "n*gga",
    "ass", "a55",

    # ── Dini Hakaretler ─────────────────────────────────────────
    "allaha küfür", "allaha sövme", "dinsiz", "imansız",
    "gavur", "kâfir",
    "piç kurusu", "it oğlu it",
    "peygambere hakaret", "kurana hakaret", "islama hakaret",
    "tanrıya küfür", "dine sövme", "allaha söveyim",
    "mevlüte küfür", "camiye küfür",
    "allah belanı versin", "allah kahretsin",
    "dini bozuk", "imansız herif",

    # ── Milliyetçilik Karşıtı / Irkçı ───────────────────────────
    "türk değil", "türkler hayvan", "türkler it",
    "kürtler hayvan", "ermeniler it", "yunanlar domuz",
    "arap pisi", "zenci", "çingene",
    "atatürk it", "atatürk domuz", "atatürke sövme",
    "vatan hain", "vatansız",

    # ── Nefret Söylemi ──────────────────────────────────────────
    "trans it", "gay pis",
    "hate speech", "kill yourself",
    "ölmesini istiyorum",
    "kendini öldür", "intihar et",

    # ── Harf Değiştirme Varyantları ─────────────────────────────
    "s1ktir", "s!ktir", "s.iktir",
    "a.mına", "a_mına", "a-mına",
    "or0spu", "0rospu",
]

# ═══════════════════════════════════════════════════════════════
#          URL / REKLAM ENGELLEYİCİ
#
#  👑 Sadece administrator yetkisine sahip kişiler:
#     → discord.gg / invite linkleri gönderebilir
#     → Hiçbir URL engelinden etkilenmez
#  👤 Normal üyeler & moderatörler:
#     → Tüm discord.gg / invite linkleri engellenir
#     → BLOCKED_DOMAINS listesindeki domainler engellenir
# ═══════════════════════════════════════════════════════════════

ALLOWED_DOMAINS = [
    "discord.gg",
    "discord.com",
    "discordapp.com",
    "projectnova.com.tr",
    "youtube.com",
    "youtu.be",
    "github.com",
    "imgur.com",
    "tenor.com",
    "giphy.com",
    "twitch.tv",
    "twitter.com",
    "x.com",
    "reddit.com",
    "spotify.com",
    "soundcloud.com",
    "instagram.com",
    "tiktok.com",
    "steam.com",
    "store.steampowered.com",
    "epicgames.com",
    "roblox.com",
]

# Kesin yasaklı domain / pattern'ler (reklam/dolandırıcılık)
BLOCKED_DOMAINS = [
    # Discord nitro dolandırıcılığı
    "discordnitro", "discord-nitro", "discord.gift",
    "discordgift", "nitro-free", "free-nitro",
    # Genel kısaltıcılar (spam amaçlı)
    "bit.ly", "tinyurl", "t.co", "ow.ly", "rb.gy",
    "cutt.ly", "shorturl", "tiny.cc", "is.gd", "buff.ly",
    # Kripto / sahte yatırım
    "crypto-free", "bitcoin-free", "btc-free",
    "coinbase-bonus", "binance-bonus", "pump-group",
    # Sahte çekilişler
    "free-robux", "freerobux", "robux-hack",
    "free-vbucks", "vbucks-hack", "freevbucks",
    # Phishing / şüpheli
    "steamcommunity.ru", "steam-trade", "steamskins",
    "csgo-skin", "skin-free",
]

# URL tespiti için regex
URL_REGEX = re.compile(
    r"(https?://[^\s<>\"]+|www\.[^\s<>\"]+|[a-zA-Z0-9\-]+\.(com|net|org|gg|io|tv|ru|xyz|tk|ml|ga|cf|gq|tr|co)[^\s]*)",
    re.IGNORECASE
)

# Discord davet linki tespiti için regex
INVITE_REGEX = re.compile(
    r"(discord\.gg/|discord\.com/invite/|dsc\.gg/|dsc\.io/)[a-zA-Z0-9]+",
    re.IGNORECASE
)

# ── Uyarı sayacı (kullanıcı başına) ───────────────────────────
warn_count:     dict = defaultdict(int)
mute_threshold: int  = 3

# ── Açık ticket takibi ─────────────────────────────────────────
open_tickets:       dict = {}
open_ozel_projeler: dict = {}
open_oncelikli:     dict = {}

# ── Invite takibi ──────────────────────────────────────────────
invite_cache: dict = {}

# ═══════════════════════════════════════════════════════════════
#                     BOT KURULUMU
# ═══════════════════════════════════════════════════════════════

intents = nextcord.Intents.default()
intents.message_content = True
intents.members         = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ═══════════════════════════════════════════════════════════════
#                       YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════

def nova_embed(title, description="", color=COLOR_PRIMARY):
    e = nextcord.Embed(title=title, description=description, color=color)
    e.set_footer(text="✦ Project Nova")
    return e

def normalize_text(text: str) -> str:
    """Harf değiştirme saldırılarını normalize et."""
    replacements = {
        "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
        "@": "a", "$": "s", "!": "i", "+": "t", "€": "e",
        "ı": "i", "ğ": "g", "ü": "u", "ş": "s", "ö": "o", "ç": "c",
    }
    result = text.lower()
    for k, v in replacements.items():
        result = result.replace(k, v)
    result = re.sub(r"[\s\.\-_\*]+", "", result)
    return result

def contains_banned_word(text: str) -> tuple[bool, str]:
    """Yasaklı kelime tespiti."""
    normalized = normalize_text(text)
    lowered    = text.lower()
    for word in BANNED_WORDS:
        clean_word = normalize_text(word)
        if clean_word in normalized:
            return True, word
        if re.search(rf"\b{re.escape(word.lower())}\b", lowered):
            return True, word
    return False, ""

def check_url(text: str) -> tuple[bool, str]:
    """Yasaklı domain kontrolü."""
    urls = URL_REGEX.findall(text)
    if not urls:
        return False, ""
    for url_match in urls:
        url = url_match[0] if isinstance(url_match, tuple) else url_match
        url_lower = url.lower()
        for blocked in BLOCKED_DOMAINS:
            if blocked in url_lower:
                return True, url
    return False, ""

def contains_invite(text: str) -> tuple[bool, str]:
    """Discord davet linki tespiti."""
    match = INVITE_REGEX.search(text)
    if match:
        return True, match.group(0)
    return False, ""

async def is_admin(interaction) -> bool:
    return interaction.user.guild_permissions.administrator

async def check_channel(interaction, allowed_id):
    if interaction.channel_id != allowed_id:
        ch = interaction.guild.get_channel(allowed_id)
        mention = ch.mention if ch else f"<#{allowed_id}>"
        await interaction.response.send_message(
            embed=nova_embed("❌  Yanlış Kanal",
                f"Bu komutu yalnızca {mention} kanalında kullanabilirsiniz.", COLOR_ERROR),
            ephemeral=True)
        return False
    return True

async def get_inviter(guild: nextcord.Guild):
    try:
        current_invites = await guild.invites()
        cached  = invite_cache.get(guild.id, {})
        inviter = None
        for invite in current_invites:
            if invite.uses > cached.get(invite.code, 0):
                inviter = invite.inviter
                break
        invite_cache[guild.id] = {inv.code: inv.uses for inv in current_invites}
        return inviter
    except Exception:
        return None

async def apply_warn(message: nextcord.Message, reason: str, detail: str = ""):
    """Uyarı ver, eşikte mute uygula, log gönder."""
    user  = message.author
    guild = message.guild
    warn_count[user.id] += 1
    count = warn_count[user.id]

    log_ch = guild.get_channel(TICKET_LOG_CH_ID)
    if log_ch:
        log_embed = nextcord.Embed(
            title="🚨  Moderasyon Kaydı",
            description=(
                f"**Kullanıcı:** {user.mention} (`{user}`)\n"
                f"**Sebep:** {reason}\n"
                f"**Detay:** `{detail[:100]}`\n"
                f"**Toplam Uyarı:** `{count}/{mute_threshold}`\n"
                f"**Kanal:** {message.channel.mention}"
            ),
            color=COLOR_ERROR
        )
        log_embed.set_thumbnail(url=user.display_avatar.url)
        log_embed.set_footer(text="✦ Project Nova — Oto-Moderasyon")
        log_embed.timestamp = nextcord.utils.utcnow()
        try:
            await log_ch.send(embed=log_embed)
        except Exception:
            pass

    if count >= mute_threshold:
        try:
            await user.edit(
                timeout=nextcord.utils.utcnow() + timedelta(minutes=10),
                reason=f"Oto-mod: {count} uyarı ({reason})"
            )
            warn_count[user.id] = 0
            warn_embed = nova_embed(
                "🔇  Otomatik Susturma",
                f"{user.mention} **{mute_threshold} uyarı** aldığı için **10 dakika** susturuldu.\n"
                f"**Son sebep:** {reason}",
                COLOR_ERROR
            )
            warn_msg = await message.channel.send(embed=warn_embed)
            await asyncio.sleep(8)
            try:
                await warn_msg.delete()
            except Exception:
                pass
        except Exception as e:
            print(f"Mute hatası: {e}")
    else:
        remaining = mute_threshold - count
        warn_embed = nova_embed(
            "⚠️  Uyarı",
            f"{user.mention} **{reason}** nedeniyle uyarıldı.\n"
            f"📌 {remaining} uyarı daha → **otomatik susturma**",
            COLOR_WARNING
        )
        warn_msg = await message.channel.send(embed=warn_embed)
        await asyncio.sleep(6)
        try:
            await warn_msg.delete()
        except Exception:
            pass

# ═══════════════════════════════════════════════════════════════
#                         OLAYLAR
# ═══════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"✅  {bot.user} olarak giriş yapıldı!")
    total = sum(g.member_count for g in bot.guilds)
    await bot.change_presence(
        activity=nextcord.Activity(
            type=nextcord.ActivityType.watching,
            name=f"{total} Üye ile Büyüyoruz 🚀"
        )
    )
    for guild in bot.guilds:
        try:
            invites = await guild.invites()
            invite_cache[guild.id] = {inv.code: inv.uses for inv in invites}
        except Exception:
            pass

@bot.event
async def on_invite_create(invite: nextcord.Invite):
    if invite.guild:
        cached = invite_cache.get(invite.guild.id, {})
        cached[invite.code] = invite.uses
        invite_cache[invite.guild.id] = cached

@bot.event
async def on_invite_delete(invite: nextcord.Invite):
    if invite.guild:
        cached = invite_cache.get(invite.guild.id, {})
        cached.pop(invite.code, None)
        invite_cache[invite.guild.id] = cached

@bot.event
async def on_member_join(member: nextcord.Member):
    guild = member.guild

    total = sum(g.member_count for g in bot.guilds)
    await bot.change_presence(
        activity=nextcord.Activity(
            type=nextcord.ActivityType.watching,
            name=f"{total} Üye ile Büyüyoruz 🚀"
        )
    )

    role = guild.get_role(AUTO_ROLE_ID)
    if role:
        try:
            await member.add_roles(role, reason="Otomatik kayıt rolü")
        except Exception as e:
            print(f"Oto rol verilemedi: {e}")

    inviter      = await get_inviter(guild)
    inviter_text = f"{inviter.mention} (`{inviter}`)" if inviter else "Bilinmiyor"

    # ── Yeni üyeye DM ─────────────────────────────────────────
    join_view   = nextcord.ui.View(timeout=None)
    btn_siparis = nextcord.ui.Button(
        label="Sipariş Oluştur",
        style=nextcord.ButtonStyle.link,
        url="https://discord.gg/gjtJv7mduX",
        emoji="🛒"
    )
    btn_website = nextcord.ui.Button(
        label="Web Sitemiz",
        style=nextcord.ButtonStyle.link,
        url="https://projectnova.com.tr",
        emoji="🌐"
    )
    join_view.add_item(btn_siparis)
    join_view.add_item(btn_website)

    join_embed = nextcord.Embed(
        title=f"🏠  Hoş geldin, {member.display_name}!",
        description=(
            f"**Project Nova | Software @2026** ailesine katıldığın için mutluyuz.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️  FiveM & Minecraft yazılım çözümleri\n"
            f"🌐  Web sitesi tasarım ve geliştirme\n"
            f"🤖  Özel Discord bot geliştirme\n"
            f"⭐  1+ yıl tecrübe · 150+ sunucu · 2.000+ sipariş\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_PRIMARY
    )
    join_embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    join_embed.set_footer(text="✦ Project Nova")

    try:
        await member.send(embed=join_embed, view=join_view)
    except Exception:
        pass

    # ── Yöneticilere bildirim ──────────────────────────────────
    admin_embed = nextcord.Embed(
        title="👤  Yeni Üye Katıldı",
        description=(
            f"**Üye:** {member.mention} (`{member}`)\n"
            f"**ID:** `{member.id}`\n"
            f"**Hesap Tarihi:** <t:{int(member.created_at.timestamp())}:R>\n"
            f"**Davet Eden:** {inviter_text}\n"
            f"**Sunucu Üye Sayısı:** `{guild.member_count}`"
        ),
        color=COLOR_SUCCESS
    )
    admin_embed.set_thumbnail(url=member.display_avatar.url)
    admin_embed.set_footer(text="✦ Project Nova — Üye Takip")
    admin_embed.timestamp = nextcord.utils.utcnow()

    for m in guild.members:
        if m.bot:
            continue
        if m.guild_permissions.administrator:
            try:
                await m.send(embed=admin_embed)
            except Exception:
                pass

@bot.event
async def on_member_remove(member):
    total = sum(g.member_count for g in bot.guilds)
    await bot.change_presence(
        activity=nextcord.Activity(
            type=nextcord.ActivityType.watching,
            name=f"{total} Üye ile Büyüyoruz 🚀"
        )
    )

@bot.event
async def on_message(message: nextcord.Message):
    if message.author.bot:
        return

    # ── Yetki seviyesi tespiti ─────────────────────────────────
    # is_admin  → sadece administrator yetkisi (discord.gg linki gönderebilir)
    # is_mod    → administrator + manage_messages + manage_guild (URL/küfür muafiyeti)
    if message.guild:
        perms    = message.author.guild_permissions
        is_admin_user = perms.administrator
        is_mod        = perms.administrator or perms.manage_messages or perms.manage_guild
    else:
        is_admin_user = False
        is_mod        = False

    # ── Embed Relay Kanalı ──────────────────────────────────────
    if message.channel.id == EMBED_RELAY_CH_ID:
        content = message.content.strip()
        try:
            await message.delete()
        except Exception:
            pass
        if content:
            relay_embed = nextcord.Embed(
                description=f"**{content}**",
                color=COLOR_PRIMARY
            )
            relay_embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url
            )
            relay_embed.set_footer(text="✦ projectnova.com.tr")
            view       = nextcord.ui.View(timeout=None)
            thanks_btn = nextcord.ui.Button(
                label="· Teşekkürler",
                style=nextcord.ButtonStyle.secondary,
                custom_id=f"thanks_{message.id}"
            )
            async def thanks_callback(inter: Interaction):
                await inter.response.send_message(
                    embed=nova_embed(
                        "🙏 Teşekkürler!",
                        f"{inter.user.mention} teşekkürlerini iletti!",
                        COLOR_SUCCESS
                    ),
                    ephemeral=True
                )
            thanks_btn.callback = thanks_callback
            view.add_item(thanks_btn)
            await message.channel.send(embed=relay_embed, view=view)
        return

    if not is_mod:
        full_text = message.content

        # ── 1. KÜFÜR / YASAKLI KELİME KONTROLÜ ────────────────
        found, word = contains_banned_word(full_text)
        if found:
            try:
                await message.delete()
            except Exception:
                pass
            await apply_warn(message, "Uygunsuz / yasaklı ifade kullanımı", word)
            return

        # ── 2. URL / REKLAM ENGELLEYİCİ ───────────────────────
        blocked_url, blocked_url_value = check_url(full_text)
        if blocked_url:
            try:
                await message.delete()
            except Exception:
                pass
            await apply_warn(message, "İzinsiz URL / reklam paylaşımı", blocked_url_value)
            return

        # ── 3. DISCORD DAVET LİNKİ KONTROLÜ ───────────────────
        # Tüm discord.gg / invite linkleri normal üyeler ve modlar için yasak.
        # Sadece administrator yetkisine sahip kişiler gönderebilir.
        has_invite, invite_val = contains_invite(full_text)
        if has_invite:
            try:
                await message.delete()
            except Exception:
                pass
            await apply_warn(message, "İzinsiz Discord davet linki paylaşımı", invite_val)
            return

    elif not is_admin_user:
        # Moderatörler küfür/URL engelinden muaf ama davet linki gönderemez
        full_text = message.content
        has_invite, invite_val = contains_invite(full_text)
        if has_invite:
            try:
                await message.delete()
            except Exception:
                pass
            await apply_warn(message, "İzinsiz Discord davet linki paylaşımı", invite_val)
            return

    await bot.process_commands(message)

# ═══════════════════════════════════════════════════════════════
#                   DOĞRULAMA SİSTEMİ
# ═══════════════════════════════════════════════════════════════

class VerifyView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(
        label="✅  Doğrula — Sunucuya Katıl",
        style=nextcord.ButtonStyle.success,
        custom_id="verify_btn"
    )
    async def verify(self, button, interaction: Interaction):
        role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        if role is None:
            return await interaction.response.send_message(
                embed=nova_embed("⚠️  Hata", "Doğrulama rolü bulunamadı.", COLOR_WARNING),
                ephemeral=True
            )
        if role in interaction.user.roles:
            return await interaction.response.send_message(
                embed=nova_embed(
                    "ℹ️  Zaten Doğrulandın",
                    "Zaten doğrulanmışsın! Sunucunun tadını çıkar 🎉",
                    COLOR_INFO
                ),
                ephemeral=True
            )

        await interaction.user.add_roles(role, reason="Doğrulama butonu")

        verify_view = nextcord.ui.View(timeout=None)
        btn_sunucu  = nextcord.ui.Button(
            label="Sunucuya Git",
            style=nextcord.ButtonStyle.link,
            url="https://discord.gg/gjtJv7mduX",
            emoji="🚀"
        )
        btn_web = nextcord.ui.Button(
            label="Web Sitemiz",
            style=nextcord.ButtonStyle.link,
            url="https://projectnova.com.tr",
            emoji="🌐"
        )
        verify_view.add_item(btn_sunucu)
        verify_view.add_item(btn_web)

        dm_embed = nextcord.Embed(
            title="✅  Doğrulama Başarılı",
            description=(
                f"**Project Nova | Software @2026** sunucusunda başarıyla doğrulandın!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅  Artık tüm kanallara erişim sağlayabilirsin\n"
                f"🎫  Yardıma ihtiyacın olursa destek talebi oluşturabilirsin\n"
                f"❤️  Topluluğumuza hoş geldin!\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=COLOR_SUCCESS
        )
        dm_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        dm_embed.set_footer(text="✦ Project Nova")

        try:
            await interaction.user.send(embed=dm_embed, view=verify_view)
        except Exception:
            pass

        await interaction.response.send_message(
            embed=nova_embed(
                "🎉  Hoş Geldin!",
                f"{interaction.user.mention} **Project Nova**'ya hoş geldin!\n\n"
                f"✅ Doğrulandın ve tüm kanallara erişim kazandın.\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 Kuralları oku ve eğlenceli zaman geçir! 🚀",
                COLOR_SUCCESS
            ),
            ephemeral=True
        )


@bot.slash_command(name="dogrulama", description="✅ Doğrulama panelini gönderir. (Admin)")
async def dogrulama(interaction: Interaction):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
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
        color=COLOR_PRIMARY
    )
    embed.set_footer(text="✦ Project Nova — Doğrulama Sistemi")
    await interaction.channel.send(embed=embed, view=VerifyView())
    await interaction.response.send_message(
        embed=nova_embed("✅ Panel Gönderildi", "Doğrulama paneli başarıyla gönderildi!", COLOR_SUCCESS),
        ephemeral=True
    )

# ═══════════════════════════════════════════════════════════════
#               TİCKET SİSTEMİ
# ═══════════════════════════════════════════════════════════════

class CloseTicketView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(
        label="🔒  Ticket'ı Kapat",
        style=nextcord.ButtonStyle.danger,
        custom_id="close_ticket_btn"
    )
    async def close_ticket(self, button: nextcord.ui.Button, interaction: Interaction):
        channel  = interaction.channel
        guild    = interaction.guild
        owner_id = None
        for uid, cid in open_tickets.items():
            if cid == channel.id:
                owner_id = uid
                break

        log_ch = guild.get_channel(TICKET_LOG_CH_ID)
        if log_ch:
            log_embed = nextcord.Embed(
                title="🔒  Ticket Kapatıldı",
                description=(
                    f"**Kanal:** {channel.name}\n"
                    f"**Kapatan:** {interaction.user.mention} (`{interaction.user}`)\n"
                    + (f"**Ticket Sahibi:** <@{owner_id}>" if owner_id else "")
                ),
                color=COLOR_ERROR
            )
            log_embed.set_footer(text="✦ Project Nova — Ticket Log")
            log_embed.timestamp = nextcord.utils.utcnow()
            try:
                await log_ch.send(embed=log_embed)
            except Exception as e:
                print(f"Log gönderilemedi: {e}")

        if owner_id:
            open_tickets.pop(owner_id, None)

        await interaction.response.send_message(
            embed=nova_embed("🔒  Kapatılıyor...", "Ticket 5 saniye içinde silinecek.", COLOR_WARNING)
        )
        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"{interaction.user} tarafından kapatıldı.")
        except Exception as e:
            print(f"Kanal silinemedi: {e}")


class TicketCategorySelect(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(label="Sipariş",             description="Yeni bir sipariş vermek istiyorum",            emoji="⭐", value="siparis"),
            nextcord.SelectOption(label="Destek",              description="Bir sorunum var, yardım istiyorum",             emoji="💫", value="destek"),
            nextcord.SelectOption(label="Proje İsteği",        description="Özel proje talebi oluşturmak istiyorum",        emoji="🌟", value="proje_istegi"),
            nextcord.SelectOption(label="Ücretsiz Proje Alma", description="Ücretsiz proje hakkında bilgi almak istiyorum", emoji="✨", value="ucretsiz_proje"),
            nextcord.SelectOption(label="Diğer",               description="Diğer konular hakkında",                       emoji="💠", value="diger"),
        ]
        super().__init__(
            placeholder="📂 Bir kategori seç...",
            min_values=1, max_values=1,
            options=options,
            custom_id="ticket_category_select"
        )

    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user  = interaction.user
        labels = {
            "siparis":        ("Sipariş",            "⭐"),
            "destek":         ("Destek",              "💫"),
            "proje_istegi":   ("Proje İsteği",        "🌟"),
            "ucretsiz_proje": ("Ücretsiz Proje Alma", "✨"),
            "diger":          ("Diğer",               "💠"),
        }
        label, emoji = labels.get(self.values[0], ("Ticket", "🎫"))

        if user.id in open_tickets:
            existing = guild.get_channel(open_tickets[user.id])
            if existing:
                return await interaction.followup.send(
                    embed=nova_embed(
                        "⚠️ Mevcut Ticket",
                        f"Zaten açık bir ticket'ın var: {existing.mention}",
                        COLOR_WARNING
                    ),
                    ephemeral=True
                )
            else:
                open_tickets.pop(user.id, None)

        category   = guild.get_channel(TICKET_CATEGORY_ID)
        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
            user:               nextcord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me:           nextcord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True),
        }

        try:
            ticket_ch = await guild.create_text_channel(
                name=f"ticket-{user.name}",
                overwrites=overwrites,
                category=category,
                topic=f"{emoji} {label} | {user} tarafından açıldı"
            )
        except Exception as e:
            return await interaction.followup.send(
                embed=nova_embed("❌ Ticket Oluşturulamadı", f"Hata:\n```{e}```", COLOR_ERROR),
                ephemeral=True
            )

        open_tickets[user.id] = ticket_ch.id
        close_view   = CloseTicketView()
        ticket_embed = nextcord.Embed(
            title=f"{emoji} {label} — Ticket Açıldı",
            description=(
                f"Merhaba {user.mention} 👋\n\n"
                f"**Kategori:** {emoji} {label}\n\n"
                f"Talebini detaylı şekilde yazabilirsin.\n"
                f"Yetkililer en kısa sürede ilgilenecek."
            ),
            color=COLOR_TICKET
        )
        ticket_embed.set_footer(text="✦ Project Nova")
        await ticket_ch.send(content=user.mention, embed=ticket_embed, view=close_view)

        log_ch = guild.get_channel(TICKET_LOG_CH_ID)
        if log_ch:
            log_embed = nextcord.Embed(
                title="📂  Yeni Ticket Açıldı",
                description=(
                    f"**Kanal:** {ticket_ch.mention}\n"
                    f"**Açan:** {user.mention} (`{user}`)\n"
                    f"**Kategori:** {emoji} {label}"
                ),
                color=COLOR_SUCCESS
            )
            log_embed.set_author(name=str(user), icon_url=user.display_avatar.url)
            log_embed.set_footer(text="✦ Project Nova — Ticket Log")
            log_embed.timestamp = nextcord.utils.utcnow()
            try:
                await log_ch.send(embed=log_embed)
            except Exception as e:
                print(f"Log gönderilemedi: {e}")

        await interaction.followup.send(
            embed=nova_embed(
                "✅ Ticket Oluşturuldu",
                f"Ticket kanalın hazır: {ticket_ch.mention}",
                COLOR_SUCCESS
            ),
            ephemeral=True
        )


class TicketView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())


@bot.slash_command(name="ticket-kur", description="🎫 Ticket panelini gönderir. (Admin)")
async def ticket_kur(interaction: Interaction):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    embed = nextcord.Embed(
        title="🎫  Destek & Ticket Sistemi",
        description=(
            "**Merhaba!** 👋\n\n"
            "Bir konuda yardım almak, sipariş vermek veya proje talebi oluşturmak için "
            "aşağıdaki menüden uygun kategoriyi seçerek ticket açabilirsin.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⭐ **Sipariş** — Yeni sipariş vermek istiyorum\n"
            "💫 **Destek** — Sorunum var, yardım istiyorum\n"
            "🌟 **Proje İsteği** — Özel proje talebi\n"
            "✨ **Ücretsiz Proje** — Ücretsiz proje bilgisi\n"
            "💠 **Diğer** — Diğer konular\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Her kullanıcı aynı anda yalnızca **1 ticket** açabilir."
        ),
        color=COLOR_TICKET
    )
    embed.set_footer(text="✦ Project Nova — Destek Sistemi")
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message(
        embed=nova_embed("✅ Panel Gönderildi", "Ticket paneli başarıyla gönderildi!", COLOR_SUCCESS),
        ephemeral=True
    )

# ═══════════════════════════════════════════════════════════════
#               ÖZEL PROJE SİSTEMİ
# ═══════════════════════════════════════════════════════════════

class OzelProjeCloseView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(
        label="🔒  Talebi Kapat",
        style=nextcord.ButtonStyle.danger,
        custom_id="close_ozel_proje_btn"
    )
    async def close_ozel_proje(self, button: nextcord.ui.Button, interaction: Interaction):
        channel  = interaction.channel
        guild    = interaction.guild
        owner_id = None
        for uid, cid in open_ozel_projeler.items():
            if cid == channel.id:
                owner_id = uid
                break

        log_ch = guild.get_channel(TICKET_LOG_CH_ID)
        if log_ch:
            log_embed = nextcord.Embed(
                title="🔒  Özel Proje Talebi Kapatıldı",
                description=(
                    f"**Kanal:** {channel.name}\n"
                    f"**Kapatan:** {interaction.user.mention} (`{interaction.user}`)\n"
                    + (f"**Talep Sahibi:** <@{owner_id}>" if owner_id else "")
                ),
                color=COLOR_ERROR
            )
            log_embed.set_footer(text="✦ Project Nova — Ticket Log")
            log_embed.timestamp = nextcord.utils.utcnow()
            try:
                await log_ch.send(embed=log_embed)
            except Exception as e:
                print(f"Log gönderilemedi: {e}")

        if owner_id:
            open_ozel_projeler.pop(owner_id, None)

        await interaction.response.send_message(
            embed=nova_embed("🔒  Kapatılıyor...", "Kanal 5 saniye içinde silinecek.", COLOR_WARNING)
        )
        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"{interaction.user} tarafından kapatıldı.")
        except Exception as e:
            print(f"Kanal silinemedi: {e}")


class OzelProjeTurSelect(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(label="Discord Botu",     description="Özel Discord botu yaptırmak istiyorum",     emoji="🤖", value="discord_bot"),
            nextcord.SelectOption(label="Web Sitesi",       description="Web sitesi veya web uygulaması istiyorum",   emoji="🌐", value="web_sitesi"),
            nextcord.SelectOption(label="Discord Sunucusu", description="Sunucu kurulumu / düzenleme istiyorum",      emoji="🏠", value="discord_sunucu"),
            nextcord.SelectOption(label="Grafik / Tasarım", description="Logo, banner veya grafik tasarım istiyorum", emoji="🎨", value="grafik"),
            nextcord.SelectOption(label="Diğer",            description="Başka bir proje talebim var",                emoji="💡", value="diger"),
        ]
        super().__init__(
            placeholder="🗂️ Proje türünü seç...",
            min_values=1, max_values=1,
            options=options,
            custom_id="ozel_proje_tur_select"
        )

    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user  = interaction.user
        labels = {
            "discord_bot":    ("Discord Botu",    "🤖"),
            "web_sitesi":     ("Web Sitesi",       "🌐"),
            "discord_sunucu": ("Discord Sunucusu", "🏠"),
            "grafik":         ("Grafik / Tasarım", "🎨"),
            "diger":          ("Diğer",            "💡"),
        }
        label, emoji = labels.get(self.values[0], ("Proje", "📁"))

        if user.id in open_ozel_projeler:
            existing = guild.get_channel(open_ozel_projeler[user.id])
            if existing:
                return await interaction.followup.send(
                    embed=nova_embed(
                        "⚠️ Mevcut Talep",
                        f"Zaten açık bir özel proje talebin var: {existing.mention}",
                        COLOR_WARNING
                    ),
                    ephemeral=True
                )
            else:
                open_ozel_projeler.pop(user.id, None)

        category   = guild.get_channel(OZEL_PROJE_CATEGORY_ID)
        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
            user:               nextcord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me:           nextcord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True),
        }

        try:
            proje_ch = await guild.create_text_channel(
                name=f"proje-{user.name}",
                overwrites=overwrites,
                category=category,
                topic=f"{emoji} {label} | {user} tarafından açıldı"
            )
        except Exception as e:
            return await interaction.followup.send(
                embed=nova_embed("❌ Kanal Oluşturulamadı", f"Hata:\n```{e}```", COLOR_ERROR),
                ephemeral=True
            )

        open_ozel_projeler[user.id] = proje_ch.id
        close_view  = OzelProjeCloseView()
        proje_embed = nextcord.Embed(
            title=f"{emoji} Özel Proje Talebi — {label}",
            description=(
                f"Merhaba {user.mention} 👋\n\n"
                f"**Proje Türü:** {emoji} {label}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Lütfen projen hakkında aşağıdakileri detaylı yaz:\n\n"
                f"📌 **Ne istiyorsun?** — Projenin amacını ve özelliklerini anlat\n"
                f"⏰ **Teslim tarihi?** — Ne zaman teslim edilmesini istiyorsun?\n"
                f"💰 **Bütçen nedir?** — Ödeme yapmayı düşünüyor musun?\n"
                f"📎 **Referans var mı?** — Örnek proje/link/görsel varsa paylaş\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Ekibimiz en kısa sürede seninle iletişime geçecek! 🚀"
            ),
            color=0xF1C40F
        )
        proje_embed.set_footer(text="✦ Project Nova — Özel Proje")
        await proje_ch.send(content=user.mention, embed=proje_embed, view=close_view)

        log_ch = guild.get_channel(TICKET_LOG_CH_ID)
        if log_ch:
            log_embed = nextcord.Embed(
                title="📁  Yeni Özel Proje Talebi",
                description=(
                    f"**Kanal:** {proje_ch.mention}\n"
                    f"**Açan:** {user.mention} (`{user}`)\n"
                    f"**Proje Türü:** {emoji} {label}"
                ),
                color=0xF1C40F
            )
            log_embed.set_author(name=str(user), icon_url=user.display_avatar.url)
            log_embed.set_footer(text="✦ Project Nova — Ticket Log")
            log_embed.timestamp = nextcord.utils.utcnow()
            try:
                await log_ch.send(embed=log_embed)
            except Exception as e:
                print(f"Log gönderilemedi: {e}")

        await interaction.followup.send(
            embed=nova_embed(
                "✅ Talep Oluşturuldu",
                f"Özel proje kanalın hazır: {proje_ch.mention}",
                COLOR_SUCCESS
            ),
            ephemeral=True
        )


class OzelProjeView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(OzelProjeTurSelect())


@bot.slash_command(name="özelproje", description="📁 Özel proje talep panelini gönderir.")
async def ozel_proje(interaction: Interaction):
    embed = nextcord.Embed(
        title="📁  Özel Proje Talebi",
        description=(
            "**Merhaba!** 👋\n\n"
            "Sana özel bir proje yaptırmak mı istiyorsun?\n"
            "Aşağıdan proje türünü seçerek talebini oluşturabilirsin.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 **Discord Botu** — Özel bot geliştirme\n"
            "🌐 **Web Sitesi** — Web sitesi / uygulama\n"
            "🏠 **Discord Sunucusu** — Sunucu kurulum & tasarım\n"
            "🎨 **Grafik / Tasarım** — Logo, banner, grafik\n"
            "💡 **Diğer** — Diğer proje talepleri\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 Her kullanıcı aynı anda yalnızca **1 talep** açabilir."
        ),
        color=0xF1C40F
    )
    embed.set_footer(text="✦ Project Nova — Özel Proje Sistemi")
    await interaction.channel.send(embed=embed, view=OzelProjeView())
    await interaction.response.send_message(
        embed=nova_embed("✅ Panel Gönderildi", "Özel proje paneli başarıyla gönderildi!", COLOR_SUCCESS),
        ephemeral=True
    )

# ═══════════════════════════════════════════════════════════════
#             ÖNCELİKLİ DESTEK SİSTEMİ
# ═══════════════════════════════════════════════════════════════

class OncelikliCloseView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(
        label="🔒  Destek Talebini Kapat",
        style=nextcord.ButtonStyle.danger,
        custom_id="close_oncelikli_btn"
    )
    async def close_oncelikli(self, button: nextcord.ui.Button, interaction: Interaction):
        channel  = interaction.channel
        guild    = interaction.guild
        owner_id = None
        for uid, cid in open_oncelikli.items():
            if cid == channel.id:
                owner_id = uid
                break

        log_ch = guild.get_channel(TICKET_LOG_CH_ID)
        if log_ch:
            log_embed = nextcord.Embed(
                title="🔒  Öncelikli Destek Talebi Kapatıldı",
                description=(
                    f"**Kanal:** {channel.name}\n"
                    f"**Kapatan:** {interaction.user.mention} (`{interaction.user}`)\n"
                    + (f"**Talep Sahibi:** <@{owner_id}>" if owner_id else "")
                ),
                color=COLOR_ERROR
            )
            log_embed.set_footer(text="✦ Project Nova — Ticket Log")
            log_embed.timestamp = nextcord.utils.utcnow()
            try:
                await log_ch.send(embed=log_embed)
            except Exception as e:
                print(f"Log gönderilemedi: {e}")

        if owner_id:
            open_oncelikli.pop(owner_id, None)

        await interaction.response.send_message(
            embed=nova_embed("🔒  Kapatılıyor...", "Kanal 5 saniye içinde silinecek.", COLOR_WARNING)
        )
        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"{interaction.user} tarafından kapatıldı.")
        except Exception as e:
            print(f"Kanal silinemedi: {e}")


class OncelikliKonuSelect(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(label="Acil Teknik Destek", description="Acil teknik bir sorunum var",                emoji="🚨", value="acil_teknik"),
            nextcord.SelectOption(label="Ödeme / Fatura",     description="Ödeme veya fatura ile ilgili sorunum var",   emoji="💳", value="odeme"),
            nextcord.SelectOption(label="VIP Sipariş",        description="Öncelikli sipariş vermek istiyorum",         emoji="👑", value="vip_siparis"),
            nextcord.SelectOption(label="Şikayet",            description="Bir şikayet iletmek istiyorum",              emoji="📣", value="sikayet"),
            nextcord.SelectOption(label="Diğer (Öncelikli)",  description="Acil başka bir konuda yardıma ihtiyacım var",emoji="⚡", value="diger"),
        ]
        super().__init__(
            placeholder="⚡ Destek konusunu seç...",
            min_values=1, max_values=1,
            options=options,
            custom_id="oncelikli_konu_select"
        )

    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user  = interaction.user
        labels = {
            "acil_teknik": ("Acil Teknik Destek", "🚨"),
            "odeme":       ("Ödeme / Fatura",      "💳"),
            "vip_siparis": ("VIP Sipariş",         "👑"),
            "sikayet":     ("Şikayet",             "📣"),
            "diger":       ("Diğer (Öncelikli)",   "⚡"),
        }
        label, emoji = labels.get(self.values[0], ("Öncelikli Destek", "⚡"))

        if user.id in open_oncelikli:
            existing = guild.get_channel(open_oncelikli[user.id])
            if existing:
                return await interaction.followup.send(
                    embed=nova_embed(
                        "⚠️ Mevcut Talep",
                        f"Zaten açık bir öncelikli destek talebin var: {existing.mention}",
                        COLOR_WARNING
                    ),
                    ephemeral=True
                )
            else:
                open_oncelikli.pop(user.id, None)

        category   = guild.get_channel(ONCELIKLI_CATEGORY_ID)
        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
            user:               nextcord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me:           nextcord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True),
        }

        try:
            destek_ch = await guild.create_text_channel(
                name=f"öncelikli-{user.name}",
                overwrites=overwrites,
                category=category,
                topic=f"{emoji} {label} | {user} tarafından açıldı"
            )
        except Exception as e:
            return await interaction.followup.send(
                embed=nova_embed("❌ Kanal Oluşturulamadı", f"Hata:\n```{e}```", COLOR_ERROR),
                ephemeral=True
            )

        open_oncelikli[user.id] = destek_ch.id
        close_view   = OncelikliCloseView()
        destek_embed = nextcord.Embed(
            title=f"{emoji} Öncelikli Destek — {label}",
            description=(
                f"Merhaba {user.mention} 👋\n\n"
                f"**Konu:** {emoji} {label}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔴 **Öncelikli destek talebin alındı!**\n\n"
                f"Ekibimiz sana en hızlı şekilde dönüş yapacak.\n"
                f"Lütfen sorunu/talebini detaylı şekilde açıkla.\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0xFF6B35
        )
        destek_embed.set_footer(text="✦ Project Nova — Öncelikli Destek")
        await destek_ch.send(content=user.mention, embed=destek_embed, view=close_view)

        log_ch = guild.get_channel(TICKET_LOG_CH_ID)
        if log_ch:
            log_embed = nextcord.Embed(
                title="⚡  Yeni Öncelikli Destek Talebi",
                description=(
                    f"**Kanal:** {destek_ch.mention}\n"
                    f"**Açan:** {user.mention} (`{user}`)\n"
                    f"**Konu:** {emoji} {label}"
                ),
                color=0xFF6B35
            )
            log_embed.set_author(name=str(user), icon_url=user.display_avatar.url)
            log_embed.set_footer(text="✦ Project Nova — Ticket Log")
            log_embed.timestamp = nextcord.utils.utcnow()
            try:
                await log_ch.send(embed=log_embed)
            except Exception as e:
                print(f"Log gönderilemedi: {e}")

        await interaction.followup.send(
            embed=nova_embed(
                "✅ Talep Oluşturuldu",
                f"Öncelikli destek kanalın hazır: {destek_ch.mention}",
                COLOR_SUCCESS
            ),
            ephemeral=True
        )


class OncelikliView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(OncelikliKonuSelect())


@bot.slash_command(name="öncelikli-destek-kur", description="⚡ Öncelikli destek panelini gönderir. (Admin)")
async def oncelikli_destek_kur(interaction: Interaction):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    embed = nextcord.Embed(
        title="⚡  Öncelikli Destek Sistemi",
        description=(
            "**Öncelikli Destek'e Hoş Geldin!** 🔴\n\n"
            "Acil veya önemli bir konuda hızlı destek almak için\n"
            "aşağıdan konunu seçerek talebini oluşturabilirsin.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🚨 **Acil Teknik Destek** — Kritik teknik sorunlar\n"
            "💳 **Ödeme / Fatura** — Ödeme ve fatura işlemleri\n"
            "👑 **VIP Sipariş** — Öncelikli sipariş\n"
            "📣 **Şikayet** — Şikayet iletmek istiyorum\n"
            "⚡ **Diğer (Öncelikli)** — Diğer acil konular\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⏱️ Ekibimiz öncelikli taleplere **en hızlı şekilde** dönüş yapar.\n"
            "📌 Her kullanıcı aynı anda yalnızca **1 talep** açabilir."
        ),
        color=0xFF6B35
    )
    embed.set_footer(text="✦ Project Nova — Öncelikli Destek Sistemi")
    await interaction.channel.send(embed=embed, view=OncelikliView())
    await interaction.response.send_message(
        embed=nova_embed("✅ Panel Gönderildi", "Öncelikli destek paneli başarıyla gönderildi!", COLOR_SUCCESS),
        ephemeral=True
    )

# ═══════════════════════════════════════════════════════════════
#                  DUYURU — /duyuru-paylas
# ═══════════════════════════════════════════════════════════════

@bot.slash_command(name="duyuru-paylas", description="📢 Duyuru kanalına mesaj gönderir. (Admin)")
async def duyuru_paylas(
    interaction: Interaction,
    mesaj: str = SlashOption(name="mesaj", description="Duyuru metni", required=True)
):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    ch = interaction.guild.get_channel(ANNOUNCEMENT_CH_ID)
    if ch is None:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Hata", "Duyuru kanalı bulunamadı.", COLOR_ERROR),
            ephemeral=True
        )
    embed = nextcord.Embed(title="📢  Yeni Duyuru", description=mesaj, color=COLOR_PRIMARY)
    embed.set_author(
        name=f"{interaction.user.display_name} tarafından",
        icon_url=interaction.user.display_avatar.url
    )
    embed.set_footer(text="✦ Project Nova — Duyuru")
    await ch.send("@everyone", embed=embed)
    await interaction.response.send_message(
        embed=nova_embed("✅ Duyuru Gönderildi", f"Duyurun {ch.mention} kanalına gönderildi!", COLOR_SUCCESS),
        ephemeral=True
    )

# ═══════════════════════════════════════════════════════════════
#            TOPLU DM MESAJ — /toplu-dm-mesaj
# ═══════════════════════════════════════════════════════════════

@bot.slash_command(name="toplu-dm-mesaj", description="📨 Sunucudaki tüm üyelere DM gönderir. (Admin)")
async def toplu_dm_mesaj(
    interaction: Interaction,
    baslik: str = SlashOption(name="baslik", description="Embed başlığı", required=True),
    mesaj:  str = SlashOption(name="mesaj",  description="Gönderilecek mesaj", required=True)
):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    await interaction.response.send_message(
        embed=nova_embed("📨 Gönderiliyor...", "Tüm üyelere DM gönderiliyor, bu biraz sürebilir...", COLOR_INFO),
        ephemeral=True
    )
    guild     = interaction.guild
    basarili  = 0
    basarisiz = 0
    dm_embed  = nextcord.Embed(title=f"📢  {baslik}", description=mesaj, color=COLOR_PRIMARY)
    dm_embed.set_author(name="Project Nova", icon_url=guild.icon.url if guild.icon else None)
    dm_embed.set_footer(text="✦ Project Nova")
    dm_embed.timestamp = nextcord.utils.utcnow()

    for member in guild.members:
        if member.bot:
            continue
        try:
            await member.send(embed=dm_embed)
            basarili += 1
            await asyncio.sleep(0.5)
        except Exception:
            basarisiz += 1

    result_embed = nextcord.Embed(
        title="📨  Toplu DM Tamamlandı",
        description=(
            f"**Başlık:** {baslik}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅  **Başarılı:** `{basarili}` kişi\n"
            f"❌  **Başarısız:** `{basarisiz}` kişi (DM kapalı)\n"
            f"👥  **Toplam:** `{basarili + basarisiz}` kişi\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_SUCCESS
    )
    result_embed.set_footer(text="✦ Project Nova — Toplu DM")
    result_embed.timestamp = nextcord.utils.utcnow()
    try:
        await interaction.user.send(embed=result_embed)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════
#            DM MESAJ — /dmmesaj
# ═══════════════════════════════════════════════════════════════

@bot.slash_command(name="dmmesaj", description="📩 Tüm sunucu üyelerine özel DM mesajı gönderir. (Admin)")
async def dmmesaj(
    interaction: Interaction,
    mesaj: str = SlashOption(name="mesaj", description="Gönderilecek mesaj", required=True)
):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    await interaction.response.send_message(
        embed=nova_embed("📩 Gönderiliyor...", "Mesajınız tüm üyelere iletiliyor...", COLOR_INFO),
        ephemeral=True
    )
    guild     = interaction.guild
    basarili  = 0
    basarisiz = 0
    dm_embed  = nextcord.Embed(description=mesaj, color=COLOR_PRIMARY)
    dm_embed.set_author(
        name=f"{interaction.user.display_name} • Project Nova",
        icon_url=interaction.user.display_avatar.url
    )
    dm_embed.set_footer(text="✦ Project Nova")
    dm_embed.timestamp = nextcord.utils.utcnow()

    for member in guild.members:
        if member.bot:
            continue
        try:
            await member.send(embed=dm_embed)
            basarili += 1
            await asyncio.sleep(0.5)
        except Exception:
            basarisiz += 1

    result_embed = nextcord.Embed(
        title="📩  DM Mesajı Tamamlandı",
        description=(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅  **Başarılı:** `{basarili}` kişi\n"
            f"❌  **Başarısız:** `{basarisiz}` kişi (DM kapalı)\n"
            f"👥  **Toplam:** `{basarili + basarisiz}` kişi\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLOR_SUCCESS
    )
    result_embed.set_footer(text="✦ Project Nova — DM Sistemi")
    result_embed.timestamp = nextcord.utils.utcnow()
    try:
        await interaction.user.send(embed=result_embed)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════
#          PARTNER BAŞVURU — /partner-basvuru
# ═══════════════════════════════════════════════════════════════

class PartnerModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title="🤝  Partner Başvuru Formu")
        self.uye_sayisi = nextcord.ui.TextInput(
            label="Sunucunuz Kaç Kişi?",
            placeholder="Örn: 500",
            max_length=10
        )
        self.everyone_limit = nextcord.ui.TextInput(
            label="Everyone Limiti (Everyone mi / Everyonesiz mi?)",
            placeholder="Örn: Everyone var / Everyone yok",
            max_length=50
        )
        self.neden_biz = nextcord.ui.TextInput(
            label="Neden Biz? (Neden Partnerlik İstiyorsunuz?)",
            placeholder="Partnerlik yapmak istemenizin sebebini yazın...",
            style=nextcord.TextInputStyle.paragraph,
            max_length=500
        )
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
            color=COLOR_PRIMARY
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="✦ Project Nova — Partner Başvuru")
        partner_ch = interaction.guild.get_channel(PARTNER_CH_ID)
        if partner_ch:
            await partner_ch.send(embed=embed)
        await interaction.response.send_message(
            embed=nova_embed(
                "✅  Başvurunuz Alındı!",
                "Partner başvurunuz başarıyla gönderildi! ✅\n"
                "Ekibimiz en kısa sürede değerlendirerek size dönüş yapacak. 🤝",
                COLOR_SUCCESS
            ),
            ephemeral=True
        )


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
            style=nextcord.TextInputStyle.paragraph,
            max_length=1000
        )
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
            color=COLOR_INFO
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="✦ Project Nova — İstek Sistemi")
        req_ch = interaction.guild.get_channel(REQUEST_CH_ID)
        if req_ch:
            msg = await req_ch.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
        await interaction.response.send_message(
            embed=nova_embed(
                "✅  İsteğiniz Alındı!",
                "İsteğiniz başarıyla iletildi! 💡\nEkibimiz en kısa sürede inceleyecek. 🙏",
                COLOR_SUCCESS
            ),
            ephemeral=True
        )


@bot.slash_command(name="istekleriniz", description="💡 İstek ve öneri formunu açar.")
async def istekleriniz(interaction: Interaction):
    if not await check_channel(interaction, REQUEST_CH_ID):
        return
    await interaction.response.send_modal(RequestModal())

# ═══════════════════════════════════════════════════════════════
#          MODERASYON — ban / kick / mute / unmute / unban
# ═══════════════════════════════════════════════════════════════

@bot.slash_command(name="ban", description="🔨 Belirtilen üyeyi sunucudan yasaklar. (Moderatör)")
async def ban(
    interaction: Interaction,
    uye: nextcord.Member = SlashOption(name="uye", description="Yasaklanacak üye", required=True),
    sebep: str = SlashOption(name="sebep", description="Yasaklama sebebi", required=False, default="Sebep belirtilmedi"),
    mesaj_silme: int = SlashOption(
        name="mesaj_silme", description="Kaç günlük mesaj silinsin? (0-7)",
        required=False, default=0, min_value=0, max_value=7
    )
):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok.", COLOR_ERROR),
            ephemeral=True
        )
    if uye.top_role >= interaction.user.top_role:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Hata", "Kendinizden üst/eşit roldekini yasaklayamazsınız!", COLOR_ERROR),
            ephemeral=True
        )
    try:
        await uye.send(embed=nova_embed(
            "🔨  Yasaklandınız",
            f"**{interaction.guild.name}** sunucusundan yasaklandınız.\n\n"
            f"**Sebep:** {sebep}\n**Yetkili:** {interaction.user}",
            COLOR_ERROR
        ))
    except Exception:
        pass
    await uye.ban(reason=f"{interaction.user}: {sebep}", delete_message_days=mesaj_silme)
    embed = nextcord.Embed(
        title="🔨  Üye Yasaklandı",
        description=(
            f"**Yasaklanan:** {uye.mention} (`{uye}`)\n"
            f"**Yetkili:** {interaction.user.mention}\n"
            f"**Sebep:** {sebep}\n"
            f"**Silinen Mesaj:** Son {mesaj_silme} gün\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Bu işlem kalıcıdır."
        ),
        color=COLOR_ERROR
    )
    embed.set_thumbnail(url=uye.display_avatar.url)
    embed.set_footer(text="✦ Project Nova — Moderasyon")
    await interaction.response.send_message(embed=embed)


@bot.slash_command(name="kick", description="👢 Belirtilen üyeyi sunucudan atar. (Moderatör)")
async def kick(
    interaction: Interaction,
    uye: nextcord.Member = SlashOption(name="uye", description="Atılacak üye", required=True),
    sebep: str = SlashOption(name="sebep", description="Atma sebebi", required=False, default="Sebep belirtilmedi")
):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok.", COLOR_ERROR),
            ephemeral=True
        )
    if uye.top_role >= interaction.user.top_role:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Hata", "Kendinizden üst/eşit roldekini atamazsınız!", COLOR_ERROR),
            ephemeral=True
        )
    try:
        await uye.send(embed=nova_embed(
            "👢  Atıldınız",
            f"**{interaction.guild.name}** sunucusundan atıldınız.\n\n"
            f"**Sebep:** {sebep}\n**Yetkili:** {interaction.user}",
            COLOR_WARNING
        ))
    except Exception:
        pass
    await uye.kick(reason=f"{interaction.user}: {sebep}")
    embed = nextcord.Embed(
        title="👢  Üye Atıldı",
        description=(
            f"**Atılan:** {uye.mention} (`{uye}`)\n"
            f"**Yetkili:** {interaction.user.mention}\n"
            f"**Sebep:** {sebep}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Üye tekrar katılabilir."
        ),
        color=COLOR_WARNING
    )
    embed.set_thumbnail(url=uye.display_avatar.url)
    embed.set_footer(text="✦ Project Nova — Moderasyon")
    await interaction.response.send_message(embed=embed)


@bot.slash_command(name="mute", description="🔇 Belirtilen üyeyi susturur. (Moderatör)")
async def mute(
    interaction: Interaction,
    uye: nextcord.Member = SlashOption(name="uye", description="Susturulacak üye", required=True),
    sure: int = SlashOption(
        name="sure", description="Süre (dakika) — 0 = kalıcı (28 gün)",
        required=False, default=0, min_value=0, max_value=40320
    ),
    sebep: str = SlashOption(name="sebep", description="Susturma sebebi", required=False, default="Sebep belirtilmedi")
):
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok.", COLOR_ERROR),
            ephemeral=True
        )
    if uye.top_role >= interaction.user.top_role:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Hata", "Kendinizden üst/eşit roldekini susturamazsınız!", COLOR_ERROR),
            ephemeral=True
        )
    sure_str = f"{sure} dakika" if sure > 0 else "Kalıcı (28 gün)"
    delta    = timedelta(minutes=sure) if sure > 0 else timedelta(days=28)
    await uye.edit(timeout=nextcord.utils.utcnow() + delta, reason=f"{interaction.user}: {sebep}")
    try:
        await uye.send(embed=nova_embed(
            "🔇  Susturuldunuz",
            f"**{interaction.guild.name}** sunucusunda susturuldunuz.\n\n"
            f"**Sebep:** {sebep}\n**Süre:** {sure_str}\n**Yetkili:** {interaction.user}",
            COLOR_WARNING
        ))
    except Exception:
        pass
    embed = nextcord.Embed(
        title="🔇  Üye Susturuldu",
        description=(
            f"**Susturulan:** {uye.mention} (`{uye}`)\n"
            f"**Yetkili:** {interaction.user.mention}\n"
            f"**Sebep:** {sebep}\n"
            f"**Süre:** {sure_str}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Süre dolunca otomatik açılır."
        ),
        color=COLOR_WARNING
    )
    embed.set_thumbnail(url=uye.display_avatar.url)
    embed.set_footer(text="✦ Project Nova — Moderasyon")
    await interaction.response.send_message(embed=embed)


@bot.slash_command(name="unmute", description="🔊 Üyenin susturmasını kaldırır. (Moderatör)")
async def unmute(
    interaction: Interaction,
    uye: nextcord.Member = SlashOption(name="uye", description="Susturması kaldırılacak üye", required=True)
):
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok.", COLOR_ERROR),
            ephemeral=True
        )
    await uye.edit(timeout=None)
    await interaction.response.send_message(
        embed=nova_embed(
            "🔊  Susturma Kaldırıldı",
            f"**Üye:** {uye.mention}\n**Yetkili:** {interaction.user.mention}",
            COLOR_SUCCESS
        )
    )


@bot.slash_command(name="unban", description="🔓 Yasaklı üyenin yasağını kaldırır. (Moderatör)")
async def unban(
    interaction: Interaction,
    kullanici_id: str = SlashOption(name="kullanici_id", description="Kullanıcı ID'si", required=True),
    sebep: str = SlashOption(name="sebep", description="Sebep", required=False, default="Sebep belirtilmedi")
):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok.", COLOR_ERROR),
            ephemeral=True
        )
    try:
        user = await bot.fetch_user(int(kullanici_id))
        await interaction.guild.unban(user, reason=f"{interaction.user}: {sebep}")
        await interaction.response.send_message(
            embed=nova_embed(
                "🔓  Yasak Kaldırıldı",
                f"**Kullanıcı:** {user} (`{user.id}`)\n"
                f"**Yetkili:** {interaction.user.mention}\n"
                f"**Sebep:** {sebep}",
                COLOR_SUCCESS
            )
        )
    except Exception as e:
        await interaction.response.send_message(
            embed=nova_embed("❌ Hata", f"Yasak kaldırılamadı: {e}", COLOR_ERROR),
            ephemeral=True
        )

# ═══════════════════════════════════════════════════════════════
#         UYARI SIFIRLA — /uyari-sifirla  (Admin)
# ═══════════════════════════════════════════════════════════════

@bot.slash_command(name="uyari-sifirla", description="🔄 Belirtilen üyenin uyarı sayısını sıfırlar. (Admin)")
async def uyari_sifirla(
    interaction: Interaction,
    uye: nextcord.Member = SlashOption(name="uye", description="Uyarısı sıfırlanacak üye", required=True)
):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    onceki             = warn_count.get(uye.id, 0)
    warn_count[uye.id] = 0
    await interaction.response.send_message(
        embed=nova_embed(
            "🔄  Uyarı Sıfırlandı",
            f"**Üye:** {uye.mention}\n**Önceki Uyarı:** `{onceki}`\n**Yeni Uyarı:** `0`",
            COLOR_SUCCESS
        )
    )

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
        color=COLOR_PRIMARY
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="✦ Project Nova — İstatistik")
    await interaction.response.send_message(embed=embed)

# ═══════════════════════════════════════════════════════════════
#     URL YÖNETİMİ — /url-whitelist  /url-blacklist  (Admin)
# ═══════════════════════════════════════════════════════════════

@bot.slash_command(name="url-whitelist", description="✅ URL engelleyiciye izin verilen domain ekle/kaldır. (Admin)")
async def url_whitelist(
    interaction: Interaction,
    islem: str  = SlashOption(name="islem", description="ekle / kaldir / listele", required=True, choices=["ekle", "kaldir", "listele"]),
    domain: str = SlashOption(name="domain", description="Örn: example.com", required=False, default="")
):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    if islem == "listele":
        liste = "\n".join(f"`{d}`" for d in ALLOWED_DOMAINS)
        return await interaction.response.send_message(
            embed=nova_embed("✅  İzin Verilen Domainler", liste or "Liste boş.", COLOR_INFO),
            ephemeral=True
        )
    if not domain:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Hata", "Domain girilmedi.", COLOR_ERROR),
            ephemeral=True
        )
    domain = domain.lower().strip().removeprefix("https://").removeprefix("http://").split("/")[0]
    if islem == "ekle":
        if domain in ALLOWED_DOMAINS:
            return await interaction.response.send_message(
                embed=nova_embed("⚠️ Zaten Var", f"`{domain}` zaten listede.", COLOR_WARNING),
                ephemeral=True
            )
        ALLOWED_DOMAINS.append(domain)
        await interaction.response.send_message(
            embed=nova_embed("✅ Eklendi", f"`{domain}` izin listesine eklendi.", COLOR_SUCCESS),
            ephemeral=True
        )
    elif islem == "kaldir":
        if domain not in ALLOWED_DOMAINS:
            return await interaction.response.send_message(
                embed=nova_embed("⚠️ Bulunamadı", f"`{domain}` listede yok.", COLOR_WARNING),
                ephemeral=True
            )
        ALLOWED_DOMAINS.remove(domain)
        await interaction.response.send_message(
            embed=nova_embed("🗑️ Kaldırıldı", f"`{domain}` izin listesinden kaldırıldı.", COLOR_SUCCESS),
            ephemeral=True
        )


@bot.slash_command(name="url-blacklist", description="🚫 URL engelleyiciye yasaklı domain ekle/kaldır. (Admin)")
async def url_blacklist(
    interaction: Interaction,
    islem: str  = SlashOption(name="islem", description="ekle / kaldir / listele", required=True, choices=["ekle", "kaldir", "listele"]),
    domain: str = SlashOption(name="domain", description="Örn: spam.com", required=False, default="")
):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    if islem == "listele":
        liste = "\n".join(f"`{d}`" for d in BLOCKED_DOMAINS)
        return await interaction.response.send_message(
            embed=nova_embed("🚫  Yasaklı Domainler", liste or "Liste boş.", COLOR_INFO),
            ephemeral=True
        )
    if not domain:
        return await interaction.response.send_message(
            embed=nova_embed("❌ Hata", "Domain girilmedi.", COLOR_ERROR),
            ephemeral=True
        )
    domain = domain.lower().strip().removeprefix("https://").removeprefix("http://").split("/")[0]
    if islem == "ekle":
        if domain in BLOCKED_DOMAINS:
            return await interaction.response.send_message(
                embed=nova_embed("⚠️ Zaten Var", f"`{domain}` zaten yasaklı listede.", COLOR_WARNING),
                ephemeral=True
            )
        BLOCKED_DOMAINS.append(domain)
        await interaction.response.send_message(
            embed=nova_embed("🚫 Eklendi", f"`{domain}` yasaklı listeye eklendi.", COLOR_SUCCESS),
            ephemeral=True
        )
    elif islem == "kaldir":
        if domain not in BLOCKED_DOMAINS:
            return await interaction.response.send_message(
                embed=nova_embed("⚠️ Bulunamadı", f"`{domain}` listede yok.", COLOR_WARNING),
                ephemeral=True
            )
        BLOCKED_DOMAINS.remove(domain)
        await interaction.response.send_message(
            embed=nova_embed("✅ Kaldırıldı", f"`{domain}` yasaklı listeden kaldırıldı.", COLOR_SUCCESS),
            ephemeral=True
        )

# ═══════════════════════════════════════════════════════════════
#          KÜFÜR YÖNETİMİ — ekle / kaldır / listele  (Admin)
# ═══════════════════════════════════════════════════════════════

@bot.slash_command(name="kufur-ekle", description="🤬 Küfür listesine yeni kelime ekle. (Admin)")
async def kufur_ekle(
    interaction: Interaction,
    kelime: str = SlashOption(name="kelime", description="Eklenecek yasaklı kelime/kısaltma", required=True)
):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    kelime = kelime.lower().strip()
    if kelime in BANNED_WORDS:
        return await interaction.response.send_message(
            embed=nova_embed("⚠️ Zaten Var", f"`{kelime}` zaten küfür listesinde.", COLOR_WARNING),
            ephemeral=True
        )
    BANNED_WORDS.append(kelime)
    await interaction.response.send_message(
        embed=nova_embed("✅ Eklendi", f"`{kelime}` küfür listesine eklendi.", COLOR_SUCCESS),
        ephemeral=True
    )


@bot.slash_command(name="kufur-kaldir", description="🗑️ Küfür listesinden kelime kaldır. (Admin)")
async def kufur_kaldir(
    interaction: Interaction,
    kelime: str = SlashOption(name="kelime", description="Kaldırılacak kelime", required=True)
):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    kelime = kelime.lower().strip()
    if kelime not in BANNED_WORDS:
        return await interaction.response.send_message(
            embed=nova_embed("⚠️ Bulunamadı", f"`{kelime}` listede yok.", COLOR_WARNING),
            ephemeral=True
        )
    BANNED_WORDS.remove(kelime)
    await interaction.response.send_message(
        embed=nova_embed("🗑️ Kaldırıldı", f"`{kelime}` küfür listesinden kaldırıldı.", COLOR_SUCCESS),
        ephemeral=True
    )


@bot.slash_command(name="kufur-listesi", description="📋 Mevcut küfür listesini gösterir. (Admin)")
async def kufur_listesi(interaction: Interaction):
    if not await is_admin(interaction):
        return await interaction.response.send_message(
            embed=nova_embed("❌ Yetki Yok", "Bu komut yalnızca adminler içindir.", COLOR_ERROR),
            ephemeral=True
        )
    chunks  = []
    current = ""
    for w in BANNED_WORDS:
        entry = f"`{w}` "
        if len(current) + len(entry) > 900:
            chunks.append(current)
            current = entry
        else:
            current += entry
    if current:
        chunks.append(current)
    embed = nextcord.Embed(
        title=f"📋  Küfür Listesi ({len(BANNED_WORDS)} kelime)",
        color=COLOR_INFO
    )
    for i, chunk in enumerate(chunks[:5]):
        embed.add_field(name=f"Grup {i+1}", value=chunk, inline=False)
    embed.set_footer(text="✦ Project Nova — Moderasyon")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ═══════════════════════════════════════════════════════════════
#                        BAŞLAT
# ═══════════════════════════════════════════════════════════════

bot.run(TOKEN)
