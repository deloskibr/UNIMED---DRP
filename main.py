import discord
from discord.ext import commands, tasks
from discord import ui
import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')

QUESTIONS = [
    {"q": "O que é Roleplay (RP)?", "opts": ["Jogar sem seguir nenhuma regra", "Interpretar um personagem dentro da realidade do servidor", "Fazer tudo que quiser dentro do jogo", "Sair do personagem quando estiver perdendo"], "ans": 1},
    {"q": "O que é Anti-RP?", "opts": ["Uma atitude que mantém a interpretação", "Uma ação que respeita a realidade do servidor", "Uma ação que quebra a lógica ou as regras do Roleplay", "Uma forma de melhorar uma ação policial"], "ans": 2},
    {"q": "O que significa 'Sem Amor à Vida'?", "opts": ["Valorizar a própria vida durante uma situação de risco", "Colocar a própria vida em risco sem se importar com as consequências", "Fugir de qualquer situação de perigo", "Sempre aceitar uma abordagem policial"], "ans": 1},
    {"q": "O que é Surf?", "opts": ["Dirigir um veículo em alta velocidade", "Ficar em cima de um veículo em movimento", "Entrar em um veículo sem autorização", "Usar uma motocicleta para fugir da polícia"], "ans": 1},
    {"q": "O que é Dark RP?", "opts": ["Um RP focado apenas em atividades policiais", "Uma forma de RP envolvendo situações e temas mais pesados, seguindo as regras do servidor", "Um modo de jogo sem regras", "Um tipo de corrida clandestina"], "ans": 1},
    {"q": "Assim que o paramédico da UNIMED chega em uma ação, o que ele deve fazer?", "opts": ["Entrar na ação imediatamente e começar os atendimentos", "Mandar o bind informando a chegada da UNIMED e aguardar a área ficar segura para realizar o atendimento", "Ajudar a polícia durante a ação", "Revistar os jogadores que estiverem caídos"], "ans": 1},
    {"q": "Em uma ação entre polícia e facção, todos estão mortos, exceto 1 membro da facção que está vivo. Quem a UNIMED deve salvar primeiro?", "opts": ["Um policial que já está morto", "O membro da facção que está vivo e necessita de atendimento", "Quem tiver mais dinheiro", "Quem estiver mais próximo, independentemente da situação"], "ans": 1},
    {"q": "Caso alguém comece a te xingar durante o RP, o que você deve fazer?", "opts": ["Xingar a pessoa de volta", "Começar uma discussão", "Manter a calma, continuar o RP e, se necessário, procurar a Staff", "Sair do servidor imediatamente"], "ans": 2},
    {"q": "Se a UNIMED chegar em um local onde ainda está acontecendo um tiroteio, o que deve fazer?", "opts": ["Entrar no meio do tiroteio para salvar os feridos", "Aguardar o local ficar seguro antes de realizar o atendimento", "Ajudar a polícia a prender os criminosos", "Sair atirando para proteger a ambulância"], "ans": 1},
    {"q": "Qual deve ser a principal função da UNIMED dentro do servidor?", "opts": ["Participar de ações criminosas", "Prender criminosos", "Realizar atendimentos e prestar serviços médicos aos jogadores", "Ajudar a polícia em perseguições"], "ans": 2},
    {"q": "Durante um atendimento, um jogador começa a ameaçar o paramédico. O que ele deve fazer?", "opts": ["Sacar uma arma e atirar", "Manter a calma, preservar a própria vida e seguir o RP", "Começar a perseguir o jogador", "Desconectar do servidor"], "ans": 1},
    {"q": "Ao encontrar vários jogadores feridos, o que o paramédico deve fazer?", "opts": ["Atender somente seus amigos", "Atender quem pagar mais", "Avaliar os feridos e seguir a prioridade de atendimento estabelecida pelas regras da UNIMED", "Atender somente policiais"], "ans": 2},
    {"q": "Um membro da UNIMED pode pegar uma arma e participar de uma ação?", "opts": ["Sim, sempre que quiser", "Sim, se estiver com a ambulância", "Não, pois sua função é prestar atendimento médico e seguir as regras da corporação", "Sim, desde que esteja sozinho"], "ans": 2},
    {"q": "Se um jogador estiver caído dentro de uma área que ainda oferece risco, o que a UNIMED deve fazer?", "opts": ["Entrar imediatamente para salvá-lo", "Aguardar a área ficar segura antes de realizar o atendimento", "Ignorar o jogador para sempre", "Entrar acompanhado de outro jogador armado"], "ans": 1},
    {"q": "Se você perceber outro jogador cometendo uma infração de RP, o que deve fazer?", "opts": ["Cometer a mesma infração para se vingar", "Começar uma discussão com o jogador", "Continuar o RP e realizar uma denúncia pelos meios oficiais do servidor", "Tentar expulsar o jogador pessoalmente"], "ans": 2}
]

class QuizView(ui.View):
    def __init__(self, user, guild, channel):
        super().__init__(timeout=600) # 10 minutos (600 segundos)
        self.user = user
        self.guild = guild
        self.channel = channel
        self.current_question = 0
        self.score = 0

    async def on_timeout(self):
        try:
            embed = discord.Embed(
                title="⏰ TEMPO ESGOTADO!",
                description="Os 10 minutos para concluir o teste se esgotaram.\nEste canal será fechado.",
                color=0xff0000
            )
            await self.channel.send(embed=embed)
            import asyncio
            await asyncio.sleep(5)
            await self.channel.delete()
        except:
            pass

    async def handle_answer(self, interaction: discord.Interaction, choice: int):
        if self.user.id != interaction.user.id:
            return

        correct = QUESTIONS[self.current_question]['ans']
        if choice == correct:
            self.score += 1

        self.current_question += 1

        if self.current_question < len(QUESTIONS):
            await self.ask_question(interaction)
        else:
            await self.finish_quiz(interaction)

    async def ask_question(self, interaction: discord.Interaction):
        q = QUESTIONS[self.current_question]
        embed = discord.Embed(title=f"Pergunta {self.current_question + 1} de 15", color=0x2ecc71)
        
        desc = f"**{q['q']}**\n\n"
        letters = ["A", "B", "C", "D"]
        for i, opt in enumerate(q['opts']):
            desc += f"**{letters[i]})** {opt}\n\n"
        
        embed.description = desc
        await interaction.response.edit_message(embed=embed, view=self)

    async def finish_quiz(self, interaction: discord.Interaction):
        total = len(QUESTIONS)
        percent = (self.score / total) * 100
        approved = percent >= 60

        if approved:
            embed = discord.Embed(
                title="✅ PARABÉNS! VOCÊ FOI APROVADO!",
                description=f"Você acertou **{self.score}** de {total} questões ({percent:.1f}%).\n\nBem-vindo à UNIMED! O seu cargo foi entregue no servidor.",
                color=0x00ff00
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
            
            try:
                role = self.guild.get_role(1545276503435124746)
                member = self.guild.get_member(self.user.id)
                if role and member:
                    await member.add_roles(role)
            except Exception as e:
                print(f"Erro ao dar cargo: {e}")
                
            # Log de Aprovação
            log_channel_id = 1545262381989363859
            log_channel = self.guild.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="ℹ️ Novo Agente Aprovado",
                    description=f"{self.user.mention} concluiu o edital com aprovação.",
                    color=0x2b2d31
                )
                
                log_embed.add_field(name="✅ Status", value="```ansi\n\u001b[1;32mAPROVADO\u001b[0m\n```", inline=False)
                log_embed.add_field(name="ℹ️ Supervisor:", value="`DIRETORIA UNIMED`", inline=False)
                log_embed.add_field(name="🏷️ Categoria", value=f"**Porcentagem:** `{percent:.0f}%`", inline=False)
                
                orientacoes = (
                    "Solicite a tag com a equipe responsável.\n"
                    "Padrão em serviço: `UNIMED | OBS | SeuNick`\n"
                    "A integração será iniciada em breve."
                )
                log_embed.add_field(name="📝 Orientações", value=orientacoes, inline=False)
                
                log_embed.set_image(url="https://media.discordapp.net/attachments/1293346011691089992/1545407385634607124/image.png?ex=6a9c0849&is=6a9ab6c9&hm=1b9f4c66e9d28fa22c19bbbc0b3fd6f7dfaf38e37c0aa9296fc94d8de0515352&=&format=webp&quality=lossless")
                
                if self.user.avatar:
                    log_embed.set_thumbnail(url=self.user.avatar.url)
                    
                log_embed.timestamp = discord.utils.utcnow()
                log_embed.set_footer(text="UNIMED DRP • Organização da Corporação")
                
                try:
                    await log_channel.send(embed=log_embed)
                except Exception as e:
                    print(f"Erro ao enviar log: {e}")
                    
            # Enviar DM para o usuário (Aprovado)
            try:
                dm_embed_app = discord.Embed(
                    title="🎉 PARABÉNS! VOCÊ FOI APROVADO!",
                    description=(
                        f"Olá {self.user.mention},\n\n"
                        "Gostaríamos de parabenizá-lo! Você foi aprovado no nosso processo seletivo e agora faz parte da **UNIMED DRP**.\n\n"
                        "Seu cargo já foi entregue no servidor.\n\n"
                        "**PRÓXIMO PASSO:**\n"
                        "Para finalizar sua integração e receber seu apelido correto, por favor, **faça o seu registro** no canal clicando no link abaixo:\n"
                        "🔗 <#1545280644593225849> ou clique [aqui](https://discord.com/channels/1545262380152397905/1545280644593225849)"
                    ),
                    color=0x2ecc71
                )
                dm_embed_app.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
                dm_embed_app.set_image(url="https://media.discordapp.net/attachments/1293346011691089992/1545407385634607124/image.png?ex=6a9c0849&is=6a9ab6c9&hm=1b9f4c66e9d28fa22c19bbbc0b3fd6f7dfaf38e37c0aa9296fc94d8de0515352&=&format=webp&quality=lossless")
                await self.user.send(embed=dm_embed_app)
            except discord.Forbidden:
                print(f"Não foi possível enviar DM para o usuário {self.user}")

        else:
            embed = discord.Embed(
                title="❌ REPROVADO",
                description=f"Você acertou **{self.score}** de {total} questões ({percent:.1f}%).\n\nÉ necessário no mínimo 60% para ser aprovado. Estude as regras e tente novamente no futuro.",
                color=0xff0000
            )
            
            # Log de Reprovação
            log_channel_id = 1545262381989363859
            log_channel = self.guild.get_channel(log_channel_id)
            if log_channel:
                log_embed_rep = discord.Embed(
                    title="ℹ️ Novo Agente Reprovado",
                    description=f"{self.user.mention} concluiu o edital com **reprovação**.",
                    color=0x2b2d31
                )
                
                log_embed_rep.add_field(name="❌ Status", value="```ansi\n\u001b[1;31mREPROVADO\u001b[0m\n```", inline=False)
                log_embed_rep.add_field(name="ℹ️ Supervisor:", value="`DIRETORIA UNIMED`", inline=False)
                log_embed_rep.add_field(name="🏷️ Categoria", value=f"**Porcentagem:** `{percent:.0f}%`", inline=False)
                
                orientacoes_rep = (
                    "O candidato não atingiu a pontuação mínima (60%).\n"
                    "Deverá estudar as regras e tentar novamente no futuro."
                )
                log_embed_rep.add_field(name="📝 Orientações", value=orientacoes_rep, inline=False)
                
                log_embed_rep.set_image(url="https://media.discordapp.net/attachments/1293346011691089992/1545408321853456444/content.png?ex=6a9c0928&is=6a9ab7a8&hm=4d75f4775173d5015a4ee4bbc78d562f56661a3a1f27bd7e7c014a23ea830f4b&=&format=webp&quality=lossless&width=2048&height=683")
                
                if self.user.avatar:
                    log_embed_rep.set_thumbnail(url=self.user.avatar.url)
                    
                log_embed_rep.timestamp = discord.utils.utcnow()
                log_embed_rep.set_footer(text="UNIMED DRP • Organização da Corporação", icon_url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
                
                try:
                    await log_channel.send(embed=log_embed_rep)
                except Exception as e:
                    print(f"Erro ao enviar log de reprovação: {e}")
                    
            # Enviar DM para o usuário (Reprovado)
            try:
                dm_embed_rep = discord.Embed(
                    title="❌ AVISO DE REPROVAÇÃO",
                    description=(
                        f"Olá {self.user.mention},\n\n"
                        "Infelizmente, você não alcançou a pontuação mínima (60%) necessária no nosso edital.\n"
                        f"Você acertou **{self.score}** de {total} questões ({percent:.1f}%).\n\n"
                        "Não desanime! Recomendamos que você **estude as regras do servidor e da corporação** e tente novamente em uma próxima oportunidade.\n\n"
                        "Boa sorte na sua próxima tentativa!"
                    ),
                    color=0xff0000
                )
                dm_embed_rep.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
                dm_embed_rep.set_image(url="https://media.discordapp.net/attachments/1293346011691089992/1545408321853456444/content.png?ex=6a9c0928&is=6a9ab7a8&hm=4d75f4775173d5015a4ee4bbc78d562f56661a3a1f27bd7e7c014a23ea830f4b&=&format=webp&quality=lossless&width=2048&height=683")
                await self.user.send(embed=dm_embed_rep)
            except discord.Forbidden:
                print(f"Não foi possível enviar DM para o usuário {self.user}")
            
        if MONGO_URI:
            try:
                await db.recrutamento.insert_one({
                    "user_id": self.user.id,
                    "user_name": str(self.user),
                    "score": self.score,
                    "percent": percent,
                    "approved": approved
                })
            except Exception as e:
                print(f"Erro ao salvar no BD: {e}")

        for child in self.children:
            child.disabled = True
            
        embed.set_footer(text="Este canal será fechado em 20 segundos.")
        await interaction.response.edit_message(embed=embed, view=self)
        
        await asyncio.sleep(20)
        try:
            await self.channel.delete()
        except:
            pass

    @discord.ui.button(label='A', style=discord.ButtonStyle.primary)
    async def btn_a(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_answer(interaction, 0)

    @discord.ui.button(label='B', style=discord.ButtonStyle.primary)
    async def btn_b(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_answer(interaction, 1)

    @discord.ui.button(label='C', style=discord.ButtonStyle.primary)
    async def btn_c(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_answer(interaction, 2)

    @discord.ui.button(label='D', style=discord.ButtonStyle.primary)
    async def btn_d(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_answer(interaction, 3)

class RecruitmentView(ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label='INICIAR RECRUTAMENTO', style=discord.ButtonStyle.success, emoji='📋', custom_id='iniciar_recrutamento_btn')
    async def iniciar_btn(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        member = guild.get_member(interaction.user.id)
        
        # Bloquear quem já é membro da UNIMED
        membro_role_id = 1545262380286611559
        if member and any(r.id == membro_role_id for r in member.roles):
            embed_negado = discord.Embed(
                title="❌ Acesso Negado",
                description="Você **já faz parte da UNIMED** e não pode realizar o recrutamento novamente.",
                color=0xff0000
            )
            return await interaction.response.send_message(embed=embed_negado, ephemeral=True)
        
        category_id = 1545278162173296730
        category = guild.get_channel(category_id)
        
        if not category:
            await interaction.response.send_message('❌ Erro: Categoria de recrutamento não configurada corretamente ou não encontrada.', ephemeral=True)
            return
            
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel_name = f"teste-{interaction.user.name}"
        
        try:
            new_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
            
            quiz_view = QuizView(user=interaction.user, guild=guild, channel=new_channel)
            
            q = QUESTIONS[0]
            embed = discord.Embed(title="Pergunta 1 de 15", color=0x2ecc71)
            desc = f"**{q['q']}**\n\n"
            letters = ["A", "B", "C", "D"]
            for i, opt in enumerate(q['opts']):
                desc += f"**{letters[i]})** {opt}\n\n"
            embed.description = desc

            await new_channel.send(content=f"{interaction.user.mention}, bem-vindo ao seu teste prático!", embed=embed, view=quiz_view)
            await interaction.response.send_message(f'✅ **Tudo pronto!** Vá para o canal {new_channel.mention} para iniciar o seu teste.', ephemeral=True)
            
            # Fechar automaticamente após 10 minutos, independente de resposta
            async def auto_fechar_canal(channel, user_mention):
                await asyncio.sleep(600)  # 10 minutos
                try:
                    embed_timeout = discord.Embed(
                        title="⏰ Tempo Esgotado",
                        description=f"{user_mention}, o tempo para o teste acabou. Este canal será fechado.",
                        color=0xff0000
                    )
                    await channel.send(embed=embed_timeout)
                    await asyncio.sleep(5)
                    await channel.delete()
                except:
                    pass  # Canal já foi deletado (quiz concluído)
                    
            asyncio.create_task(auto_fechar_canal(new_channel, interaction.user.mention))
        except Exception as e:
            import sys
            print(f"Erro ao criar canal: {e}", flush=True)
            await interaction.response.send_message('❌ Erro ao criar o seu canal de recrutamento.', ephemeral=True)

# ----------------- PAINEL DE REGISTRO -----------------

PALAVRAS_OFENSIVAS = [
    "merda", "porra", "caralho", "buceta", "puta", "viado", "corno", "arrombado", 
    "fdp", "cuzao", "fuder", "foda", "pica", "cu", "rola", "cacete", "piranha"
]

def tem_palavra_ofensiva(texto):
    texto_limpo = texto.lower()
    for palavra in PALAVRAS_OFENSIVAS:
        # Verifica se a palavra está no texto
        if palavra in texto_limpo:
            return True
    return False

class RegistrationModal(ui.Modal, title='Registro de Membro'):
    nome = ui.TextInput(label='Nome no Jogo (Nome e Sobrenome)', style=discord.TextStyle.short)
    passaporte = ui.TextInput(label='Passaporte (ID)', style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        nome_jogo = self.nome.value
        id_jogo = self.passaporte.value

        if tem_palavra_ofensiva(nome_jogo):
            await interaction.response.send_message('❌ **Aviso:** O nome escolhido contém palavras inapropriadas. Por favor, tente novamente com um nome válido.', ephemeral=True)
            return

        novo_apelido = f"「UNIMED」{nome_jogo}「{id_jogo}」"
        member = interaction.guild.get_member(interaction.user.id)
        
        role_remover = interaction.guild.get_role(1545276503435124746)
        role_add_1 = interaction.guild.get_role(1545262380286611559)
        role_add_2 = interaction.guild.get_role(1545262380286611561)
        role_add_3 = interaction.guild.get_role(1545414243338166332)
        
        try:
            if role_remover:
                await member.remove_roles(role_remover)
            if role_add_1:
                await member.add_roles(role_add_1)
            if role_add_2:
                await member.add_roles(role_add_2)
            if role_add_3:
                await member.add_roles(role_add_3)
                
            # Tenta alterar o apelido do membro
            await interaction.user.edit(nick=novo_apelido)
            
            embed_sucesso = discord.Embed(
                title="✅ Registro Concluído!",
                description=(
                    "Seu registro foi finalizado com sucesso!\n"
                    "Seu apelido e cargos foram atualizados.\n\n"
                    "👉 **Próximo passo:**\n"
                    "Vá para o canal de integração:\n"
                    "🔗 <#1545405480929730572> ou [clique aqui](https://discord.com/channels/1545262380152397905/1545405480929730572)"
                ),
                color=0x2ecc71
            )
            await interaction.response.send_message(embed=embed_sucesso, ephemeral=True)
            
            # Salvar no BD
            if MONGO_URI:
                await db.membros.update_one(
                    {"user_id": interaction.user.id},
                    {"$set": {"nome_jogo": nome_jogo, "id_jogo": id_jogo, "apelido": novo_apelido}},
                    upsert=True
                )
            
            # Log de registro
            import datetime
            log_channel = interaction.guild.get_channel(1545405622688686160)
            if log_channel:
                time_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                log_embed = discord.Embed(
                    title="📋 Novo Registro",
                    color=0x2ecc71
                )
                log_embed.add_field(name="👤 Usuário", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
                log_embed.add_field(name="🎮 Nome escolhido", value=f"`{nome_jogo}`", inline=True)
                log_embed.add_field(name="🪪 ID (Passaporte)", value=f"`{id_jogo}`", inline=True)
                log_embed.add_field(name="🕐 Data/Hora", value=time_str, inline=False)
                log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                await log_channel.send(embed=log_embed)
        except discord.Forbidden:
            embed_erro_perm = discord.Embed(
                title="✅ Registro Salvo!",
                description=(
                    "Seu registro foi salvo, porém eu não tenho permissão para alterar o seu apelido ou cargos automaticamente (verifique a hierarquia do meu cargo no servidor).\n\n"
                    "👉 **Próximo passo:**\n"
                    "Mesmo assim, vá para o canal de integração:\n"
                    "🔗 <#1545405480929730572> ou [clique aqui](https://discord.com/channels/1545262380152397905/1545405480929730572)"
                ),
                color=0xf1c40f
            )
            await interaction.response.send_message(embed=embed_erro_perm, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message('❌ Ocorreu um erro ao processar seu registro.', ephemeral=True)
            import sys
            print(f"Erro no registro: {e}", flush=True)

class RegistrationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label='REGISTRE-SE AQUI', style=discord.ButtonStyle.primary, emoji='📝', custom_id='registro_btn')
    async def registrar_btn(self, interaction: discord.Interaction, button: ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        role_required_id = 1545276503435124746
        
        has_role = any(role.id == role_required_id for role in member.roles)
        if not has_role:
            await interaction.response.send_message('❌ **Acesso Negado:** Você precisa ser aprovado no recrutamento (ter o cargo necessário) para se registrar.', ephemeral=True)
            return
            
        await interaction.response.send_modal(RegistrationModal())

class AssumirTagView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='ASSUMIR', style=discord.ButtonStyle.primary, emoji='🤝', custom_id='assumir_tag_btn')
    async def assumir_btn(self, interaction: discord.Interaction, button: ui.Button):
        role_required_id = 1545415341365006487
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not any(r.id == role_required_id for r in member.roles):
            embed_erro = discord.Embed(
                title="❌ Acesso Negado",
                description="Você não possui o cargo necessário para assumir esta solicitação.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            return

        if not MONGO_URI:
            await interaction.response.send_message("❌ Banco de dados não configurado.", ephemeral=True)
            return
            
        req = await db.tag_requests.find_one({"message_id": interaction.message.id})
        if not req:
            await interaction.response.send_message("❌ Solicitação não encontrada no banco de dados.", ephemeral=True)
            return
            
        if req.get("status") == "assumida":
            await interaction.response.send_message("❌ Esta solicitação já foi assumida.", ephemeral=True)
            return

        requester_id = req["user_id"]
        requester = interaction.guild.get_member(requester_id)
        
        category_id = 1545415098271662200
        category = interaction.guild.get_channel(category_id)
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if requester:
            overwrites[requester] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
        nome_base = requester.name.lower() if requester else str(requester_id)
        trans_table = str.maketrans("abcdefghijklmnopqrstuvwxyz", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ")
        nome_canal = f"🏷️・ᴛᴀɢ- {nome_base.translate(trans_table)}"
        
        try:
            novo_canal = await interaction.guild.create_text_channel(name=nome_canal, category=category, overwrites=overwrites)
            
            await db.tag_requests.update_one(
                {"message_id": interaction.message.id},
                {"$set": {"status": "assumida", "staff_id": interaction.user.id, "channel_id": novo_canal.id}}
            )
            
            await interaction.message.delete()
            
            embed_chat = discord.Embed(
                title="🤝 Atendimento Iniciado",
                description=f"{requester.mention if requester else 'Usuário'}, sua solicitação foi assumida por {interaction.user.mention}.\nPor favor, informe os detalhes necessários para setar sua tag.",
                color=0x3498db
            )
            await novo_canal.send(content=f"{requester.mention if requester else ''} {interaction.user.mention}", embed=embed_chat, view=AtendimentoTagView())
            
            await interaction.response.send_message(f"✅ Solicitação assumida com sucesso! Vá para {novo_canal.mention}.", ephemeral=True)
            
        except Exception as e:
            print(f"Erro ao assumir tag: {e}")
            await interaction.response.send_message("❌ Erro ao criar o canal de atendimento.", ephemeral=True)

class AtendimentoTagView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def check_staff(self, interaction: discord.Interaction):
        role_required_id = 1545415341365006487
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not any(r.id == role_required_id for r in member.roles):
            embed_erro = discord.Embed(
                title="❌ Acesso Negado",
                description="Você não possui o cargo necessário para utilizar estes botões.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            return False
        return True

    async def get_requester_id(self, interaction: discord.Interaction):
        if not MONGO_URI: return None
        req = await db.tag_requests.find_one({"channel_id": interaction.channel.id})
        if req:
            return req["user_id"]
        return None

    @discord.ui.button(label='Notificar Usuário', style=discord.ButtonStyle.primary, emoji='🔔', custom_id='notificar_user_btn')
    async def notificar_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_staff(interaction):
            return
            
        requester_id = await self.get_requester_id(interaction)
        if requester_id:
            requester = interaction.guild.get_member(requester_id)
            if requester:
                try:
                    dm_embed = discord.Embed(
                        title="🔔 Notificação de Atendimento",
                        description=f"Olá {requester.mention},\n\nO responsável {interaction.user.mention} está aguardando você no seu canal de atendimento ({interaction.channel.mention}) para setar sua tag.\n\nPor favor, compareça assim que possível!",
                        color=0xf1c40f
                    )
                    await requester.send(embed=dm_embed)
                    await interaction.response.send_message(f"✅ Usuário notificado com sucesso na DM!", ephemeral=True)
                    return
                except discord.Forbidden:
                    await interaction.response.send_message(f"❌ Não foi possível enviar DM para o usuário, ele pode estar com mensagens diretas fechadas.", ephemeral=True)
                    return
        await interaction.response.send_message("❌ Usuário não encontrado no servidor ou banco de dados.", ephemeral=True)

    @discord.ui.button(label='Tag Setada', style=discord.ButtonStyle.success, emoji='✅', custom_id='tag_setada_btn')
    async def tag_setada_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_staff(interaction):
            return
            
        requester_id = await self.get_requester_id(interaction)
        if requester_id:
            requester = interaction.guild.get_member(requester_id)
            if requester:
                role_to_remove = interaction.guild.get_role(1545414243338166332)
                if role_to_remove:
                    try:
                        await requester.remove_roles(role_to_remove)
                    except Exception as e:
                        print(f"Erro ao remover cargo: {e}")
                        
            if MONGO_URI:
                await db.tag_requests.delete_one({"channel_id": interaction.channel.id})
                
            log_concluido_channel = interaction.guild.get_channel(1545405580867407923)
            if log_concluido_channel:
                import datetime
                agora = datetime.datetime.now()
                embed_log = discord.Embed(
                    title="✅ Tag Setada",
                    color=0x2ecc71
                )
                embed_log.add_field(name="Responsável", value=interaction.user.mention, inline=True)
                embed_log.add_field(name="Usuário", value=requester.mention if requester else f"ID: {requester_id}", inline=True)
                embed_log.add_field(name="Data/Horário", value=agora.strftime("%d/%m/%Y às %H:%M:%S"), inline=False)
                await log_concluido_channel.send(embed=embed_log)

        embed_fechar = discord.Embed(
            title="✅ Tag Setada",
            description="Processo concluído com sucesso. O cargo do usuário foi removido e este canal será fechado em 5 segundos...",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed_fechar)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

    @discord.ui.button(label='Fechar Ticket', style=discord.ButtonStyle.danger, emoji='🔒', custom_id='fechar_ticket_tag_btn')
    async def fechar_ticket_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_staff(interaction):
            return
            
        if MONGO_URI:
            await db.tag_requests.delete_one({"channel_id": interaction.channel.id})
            
        embed_fechar = discord.Embed(
            title="🔒 Ticket Fechado",
            description="Este canal será fechado em 5 segundos (o cargo do usuário foi mantido)...",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed_fechar)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass


class TagRequestView(ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label='SOLICITAR TAG', style=discord.ButtonStyle.success, emoji='🏷️', custom_id='solicitar_tag_btn')
    async def solicitar_btn(self, interaction: discord.Interaction, button: ui.Button):
        role_required_id = 1545414243338166332
        member = interaction.guild.get_member(interaction.user.id)
        
        has_role = any(role.id == role_required_id for role in member.roles)
        if not has_role:
            embed_erro = discord.Embed(
                title="❌ Acesso Negado",
                description=f"Você não possui o cargo necessário (<@&{role_required_id}>) para solicitar a tag. Certifique-se de realizar o seu registro primeiro.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            return
            
        if MONGO_URI:
            ja_solicitou = await db.tag_requests.find_one({"user_id": interaction.user.id})
            if ja_solicitou:
                if ja_solicitou.get("status") == "pendente":
                    old_msg_id = ja_solicitou.get("message_id")
                    if old_msg_id:
                        log_tag_channel = interaction.guild.get_channel(1545415718193860659)
                        if log_tag_channel:
                            try:
                                old_msg = await log_tag_channel.fetch_message(old_msg_id)
                                await old_msg.delete()
                            except:
                                pass
                    await db.tag_requests.delete_one({"user_id": interaction.user.id})
                else:
                    await interaction.response.send_message('❌ Você já possui um atendimento de tag em andamento!', ephemeral=True)
                    return
                
        try:
            dm_embed = discord.Embed(
                title="🏷️ Solicitação de Tag Enviada",
                description=(
                    f"Olá {interaction.user.mention},\n\n"
                    "Sua solicitação de tag no jogo foi enviada com sucesso!\n\n"
                    "Por favor, **aguarde um responsável** setar a sua tag no jogo e aceitar sua solicitação."
                ),
                color=0x3498db
            )
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            pass
            
        embed_sucesso = discord.Embed(
            title="✅ Solicitação Enviada!",
            description="Sua solicitação foi enviada com sucesso!\nPor favor, **verifique sua DM (Mensagens Diretas)** para mais detalhes.",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed_sucesso, ephemeral=True)
        
        log_tag_channel = interaction.guild.get_channel(1545415718193860659) 
        if log_tag_channel:
            import datetime
            agora = datetime.datetime.now()
            staff_embed = discord.Embed(
                title="🔔 Nova Solicitação de Tag",
                description=f"O membro {interaction.user.mention} solicitou a tag no jogo.",
                color=0xf1c40f
            )
            staff_embed.add_field(name="Data", value=agora.strftime("%d/%m/%Y"), inline=True)
            staff_embed.add_field(name="Horário", value=agora.strftime("%H:%M:%S"), inline=True)
            staff_embed.add_field(name="ID do Usuário", value=str(interaction.user.id), inline=False)
            
            msg = await log_tag_channel.send(content="<@&1545415341365006487>", embed=staff_embed, view=AssumirTagView())
            
            if MONGO_URI:
                await db.tag_requests.insert_one({
                    "user_id": interaction.user.id,
                    "user_name": str(interaction.user),
                    "status": "pendente",
                    "message_id": msg.id
                })

class ModAddRemoveModal(ui.Modal):
    def __init__(self, action: str):
        self.action = action
        super().__init__(title=f"{'Adicionar' if action == 'add' else 'Remover'} Horas")
        self.user_id = ui.TextInput(label="ID do Usuário", required=True)
        self.hours = ui.TextInput(label="Qtd em horas (ex: 1 ou 1.5)", required=True)
        self.add_item(self.user_id)
        self.add_item(self.hours)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.user_id.value.strip())
            h = float(self.hours.value.replace(',', '.').strip())
            secs = int(h * 3600)
            if self.action == "remove":
                secs = -secs
            
            if not MONGO_URI: return
            await db.bate_ponto_horas.update_one(
                {"user_id": uid},
                {"$inc": {"total_seconds": secs}},
                upsert=True
            )
            acao = "adicionadas ao" if self.action == "add" else "removidas do"
            await interaction.response.send_message(f"✅ {h} horas foram {acao} usuário {uid}.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ ID ou quantidade de horas inválida.", ephemeral=True)

class ModCloseModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Fechar Ponto Forçadamente")
        self.user_id = ui.TextInput(label="ID do Usuário", required=True)
        self.add_item(self.user_id)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.user_id.value.strip())
        except:
            return await interaction.response.send_message("❌ ID inválido.", ephemeral=True)
        
        if not MONGO_URI: return
        bp_ativo = await db.bate_ponto.find_one({"user_id": uid})
        if not bp_ativo:
            return await interaction.response.send_message("❌ Este usuário não possui ponto aberto.", ephemeral=True)

        import datetime
        agora = datetime.datetime.now()
        inicio = bp_ativo["start_time"]
        diff = agora - inicio
        
        horas, remainder = divmod(int(diff.total_seconds()), 3600)
        minutos, segundos = divmod(remainder, 60)
        total_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"

        if bp_ativo.get("channel_id") and bp_ativo.get("message_id"):
            log_channel = interaction.guild.get_channel(bp_ativo["channel_id"])
            if log_channel:
                try:
                    msg = await log_channel.fetch_message(bp_ativo["message_id"])
                    texto_log = (
                        f"<:USER:1545273489378910281> **MEMBRO:** <@{uid}>\n"
                        f"<:mas:1545273487139274853> **INÍCIO:** {inicio.strftime('%H:%M')}\n"
                        f"<:bp:1545273485348315156> **TÉRMINO:** {agora.strftime('%H:%M')}\n"
                        f"<:relogio:1545273488514748536> **TOTAL:** {total_str}\n\n"
                        f"🛡️ *Ponto fechado forçadamente pela moderação*"
                    )
                    await msg.edit(content=texto_log)
                except:
                    pass

        await db.bate_ponto_horas.update_one(
            {"user_id": uid},
            {"$inc": {"total_seconds": int(diff.total_seconds())}},
            upsert=True
        )
        await db.bate_ponto.delete_one({"user_id": uid})
        await interaction.response.send_message(f"✅ Ponto do usuário {uid} fechado com sucesso!", ephemeral=True)

class ModZeroMemberModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Zerar Horas de Membro")
        self.user_id = ui.TextInput(label="ID do Usuário", required=True)
        self.add_item(self.user_id)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.user_id.value.strip())
        except:
            return await interaction.response.send_message("❌ ID inválido.", ephemeral=True)
            
        if not MONGO_URI: return
        await db.bate_ponto_horas.delete_one({"user_id": uid})
        await interaction.response.send_message(f"✅ As horas do usuário {uid} foram zeradas.", ephemeral=True)

class ModZeroAllModal(ui.Modal):
    def __init__(self):
        super().__init__(title="Zerar TODAS as Horas")
        self.confirm = ui.TextInput(label="Digite 'CONFIRMAR'", placeholder="Apagará as horas de TODOS os membros!", required=True)
        self.add_item(self.confirm)

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirm.value == "CONFIRMAR":
            if not MONGO_URI: return
            await db.bate_ponto_horas.delete_many({})
            await interaction.response.send_message("✅ Todas as horas de todos os membros foram zeradas com sucesso!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Operação cancelada. Confirmação incorreta.", ephemeral=True)

class ModeracaoBatePontoView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='TIRAR HORA', style=discord.ButtonStyle.danger)
    async def rem_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModAddRemoveModal("remove"))

    @discord.ui.button(label='ADICIONAR', style=discord.ButtonStyle.success)
    async def add_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModAddRemoveModal("add"))

    @discord.ui.button(label='FECHAR PONTO', style=discord.ButtonStyle.primary)
    async def close_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModCloseModal())

    @discord.ui.button(label='ZERAR MEMBRO', style=discord.ButtonStyle.secondary)
    async def zero_mem_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModZeroMemberModal())

    @discord.ui.button(label='ZERAR TOTAL', style=discord.ButtonStyle.danger, row=1)
    async def zero_all_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ModZeroAllModal())

class BatePontoView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='INICIAR', style=discord.ButtonStyle.success, emoji='🚀', custom_id='bp_iniciar_btn')
    async def iniciar_btn(self, interaction: discord.Interaction, button: ui.Button):
        role_required_id = 1545262380286611559
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not any(r.id == role_required_id for r in member.roles):
            embed_erro = discord.Embed(title="❌ Acesso Negado", description="Você não possui o cargo necessário para bater ponto.", color=0xff0000)
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)

        if not MONGO_URI:
            return await interaction.response.send_message("❌ Banco de dados não configurado.", ephemeral=True)

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ Você precisa estar em uma call para iniciar o ponto!", ephemeral=True)
            
        if interaction.user.voice.channel.category_id != 1545262381804818432:
            return await interaction.response.send_message("❌ Você precisa estar em uma call da categoria PATRULHAMENTO para iniciar o ponto!", ephemeral=True)

        bp_ativo = await db.bate_ponto.find_one({"user_id": interaction.user.id})
        if bp_ativo:
            return await interaction.response.send_message("❌ Você já possui um ponto aberto!", ephemeral=True)

        import datetime
        agora = datetime.datetime.now()
        
        log_channel = interaction.guild.get_channel(1545410216231829514)
        
        texto_log = (
            f"<:USER:1545273489378910281> **MEMBRO:** {interaction.user.mention}\n"
            f"<:mas:1545273487139274853> **INÍCIO:** {agora.strftime('%H:%M')}\n"
            f"<:bp:1545273485348315156> **TÉRMINO:** --:--\n"
            f"<:relogio:1545273488514748536> **TOTAL:** --:--:--"
        )
        msg = None
        if log_channel:
            msg = await log_channel.send(texto_log)

        await db.bate_ponto.insert_one({
            "user_id": interaction.user.id,
            "start_time": agora,
            "message_id": msg.id if msg else None,
            "channel_id": log_channel.id if log_channel else None
        })

        await interaction.response.send_message(f"✅ Ponto iniciado às {agora.strftime('%H:%M')}.", ephemeral=True)

    @discord.ui.button(label='FECHAR', style=discord.ButtonStyle.danger, emoji='🛑', custom_id='bp_fechar_btn')
    async def fechar_btn(self, interaction: discord.Interaction, button: ui.Button):
        role_required_id = 1545262380286611559
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not any(r.id == role_required_id for r in member.roles):
            embed_erro = discord.Embed(title="❌ Acesso Negado", description="Você não possui o cargo necessário para bater ponto.", color=0xff0000)
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)

        if not MONGO_URI: return

        bp_ativo = await db.bate_ponto.find_one({"user_id": interaction.user.id})
        if not bp_ativo:
            return await interaction.response.send_message("❌ Você não possui nenhum ponto aberto!", ephemeral=True)

        import datetime
        agora = datetime.datetime.now()
        inicio = bp_ativo["start_time"]
        diff = agora - inicio
        
        horas, remainder = divmod(int(diff.total_seconds()), 3600)
        minutos, segundos = divmod(remainder, 60)
        total_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"

        if bp_ativo.get("channel_id") and bp_ativo.get("message_id"):
            log_channel = interaction.guild.get_channel(bp_ativo["channel_id"])
            if log_channel:
                try:
                    msg = await log_channel.fetch_message(bp_ativo["message_id"])
                    texto_log = (
                        f"<:USER:1545273489378910281> **MEMBRO:** {interaction.user.mention}\n"
                        f"<:mas:1545273487139274853> **INÍCIO:** {inicio.strftime('%H:%M')}\n"
                        f"<:bp:1545273485348315156> **TÉRMINO:** {agora.strftime('%H:%M')}\n"
                        f"<:relogio:1545273488514748536> **TOTAL:** {total_str}"
                    )
                    await msg.edit(content=texto_log)
                except Exception as e:
                    print(f"Erro ao editar ponto: {e}")

        await db.bate_ponto_horas.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {"total_seconds": int(diff.total_seconds())}},
            upsert=True
        )

        await db.bate_ponto.delete_one({"user_id": interaction.user.id})
        await interaction.response.send_message(f"✅ Ponto fechado! Total de tempo: {total_str}", ephemeral=True)

    @discord.ui.button(label='HORAS', style=discord.ButtonStyle.primary, emoji='⏱️', custom_id='bp_horas_btn')
    async def horas_btn(self, interaction: discord.Interaction, button: ui.Button):
        role_required_id = 1545262380286611559
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not any(r.id == role_required_id for r in member.roles):
            embed_erro = discord.Embed(title="❌ Acesso Negado", description="Você não possui o cargo necessário para ver suas horas.", color=0xff0000)
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            
        if not MONGO_URI:
            return await interaction.response.send_message("❌ Banco de dados não configurado.", ephemeral=True)
        
        user_data = await db.bate_ponto_horas.find_one({"user_id": interaction.user.id})
        total_secs = user_data.get("total_seconds", 0) if user_data else 0
        
        horas, remainder = divmod(total_secs, 3600)
        minutos, segundos = divmod(remainder, 60)
        
        embed = discord.Embed(
            title="⏱️ Suas Horas Totais",
            description=f"Você possui um total acumulado de **{horas:02d}h {minutos:02d}m {segundos:02d}s** registrados em serviço.",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label='MODERAÇÃO', style=discord.ButtonStyle.secondary, emoji='🛡️', custom_id='bp_mod_btn')
    async def mod_btn(self, interaction: discord.Interaction, button: ui.Button):
        mod_role = 1545424671330009189
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not any(r.id == mod_role for r in member.roles):
            embed_erro = discord.Embed(title="❌ Acesso Negado", description="Apenas a moderação pode usar isto.", color=0xff0000)
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            
        embed_mod = discord.Embed(
            title="🛡️ Painel de Moderação",
            description="Selecione abaixo a ação que deseja realizar.",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed_mod, view=ModeracaoBatePontoView(), ephemeral=True)

class AdvModal(ui.Modal):
    def __init__(self, target_member: discord.Member, adv_level: str, adv_role_id: int):
        super().__init__(title=f"Aplicar {adv_level}")
        self.target_member = target_member
        self.adv_level = adv_level
        self.adv_role_id = adv_role_id
        
        self.motivo = ui.TextInput(label="Motivo da Advertência", style=discord.TextStyle.paragraph, required=True)
        self.provas = ui.TextInput(label="Provas (Links)", style=discord.TextStyle.short, required=True)
        
        self.add_item(self.motivo)
        self.add_item(self.provas)

    async def on_submit(self, interaction: discord.Interaction):
        # Garante que o target_member seja resolvido como Member
        member = interaction.guild.get_member(self.target_member.id)
        if not member:
            return await interaction.response.send_message("❌ Membro não encontrado no servidor.", ephemeral=True)

        role = interaction.guild.get_role(self.adv_role_id)
        if role:
            try:
                await member.add_roles(role)
            except Exception as e:
                print(f"Erro ao adicionar cargo: {e}")
                return await interaction.response.send_message(f"❌ Erro ao setar a tag de advertência no membro. Verifique se as minhas permissões são mais altas que as do cargo! (Erro: {e})", ephemeral=True)
        else:
            return await interaction.response.send_message(f"❌ Cargo de advertência (ID: {self.adv_role_id}) não foi encontrado no servidor.", ephemeral=True)
                
        desc = (
            f"👤 **ADVERTIDO:** {self.target_member.mention} (`{self.target_member.id}`)\n"
            f"🏷️ **TIPO:** <@&{self.adv_role_id}>\n"
            f"📋 **MOTIVO:** {self.motivo.value}\n"
            f"🔗 **PROVA:** {self.provas.value}\n"
            f"🛡️ **RESPONSÁVEL:** {interaction.user.mention}"
        )
        
        embed = discord.Embed(
            title="",
            description=desc,
            color=0xe74c3c
        )
        avatar_url = self.target_member.display_avatar.url if self.target_member.display_avatar else None
        embed.set_author(name="⚠️ SISTEMA DE PUNIÇÕES - ADVERTÊNCIA", icon_url=avatar_url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
        embed.set_footer(text="UNIMED DRP - Departamento Pessoal")
        
        log_channel = interaction.guild.get_channel(1545262381096116319)
        if log_channel:
            await log_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ {self.adv_level} aplicada com sucesso a {self.target_member.display_name} e registrada no canal {log_channel.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ {self.adv_level} aplicada, mas o canal de logs não foi encontrado.", ephemeral=True)

class AdvSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.target_member = None
        self.adv_level = None
        self.adv_role_id = None
        
        self.user_select = ui.UserSelect(placeholder="Selecione o membro", min_values=1, max_values=1)
        self.user_select.callback = self.user_callback
        self.add_item(self.user_select)
        
        options = [
            discord.SelectOption(label="ADV 1", description="Aplicar Advertência 1", value="1545262380152397911"),
            discord.SelectOption(label="ADV 2", description="Aplicar Advertência 2", value="1545262380152397910"),
            discord.SelectOption(label="ADV 3", description="Aplicar Advertência 3", value="1545439999132958740")
        ]
        self.adv_select = ui.Select(placeholder="Selecione o tipo de ADV", min_values=1, max_values=1, options=options)
        self.adv_select.callback = self.adv_callback
        self.add_item(self.adv_select)
        
    async def user_callback(self, interaction: discord.Interaction):
        self.target_member = self.user_select.values[0]
        
        member = interaction.guild.get_member(self.target_member.id)
        if not member:
            return await interaction.response.defer()
            
        adv1 = 1545262380152397911
        adv2 = 1545262380152397910
        adv3 = 1545439999132958740
        
        has_adv1 = any(r.id == adv1 for r in member.roles)
        has_adv2 = any(r.id == adv2 for r in member.roles)
        has_adv3 = any(r.id == adv3 for r in member.roles)
        
        if has_adv3:
            self.adv_select.options = [discord.SelectOption(label="Lotação Máxima (ADV 3)", value="none")]
            self.adv_select.disabled = True
            self.adv_select.placeholder = "Consulte para Exoneração"
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            await interaction.response.edit_message(content="❌ **O membro selecionado já possui ADV 3!**\nNão é possível aplicar mais advertências. Será necessário consultar a chefia para possível **Exoneração**.", view=self)
            return

        new_options = []
        if not has_adv1 and not has_adv2:
            new_options.append(discord.SelectOption(label="ADV 1", description="Aplicar Advertência 1", value=str(adv1)))
        
        if not has_adv2:
            new_options.append(discord.SelectOption(label="ADV 2", description="Aplicar Advertência 2", value=str(adv2)))
            
        new_options.append(discord.SelectOption(label="ADV 3", description="Aplicar Advertência 3", value=str(adv3)))
        
        self.adv_select.options = new_options
        self.adv_select.disabled = False
        self.adv_select.placeholder = "Selecione o tipo de ADV"
        
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = False
                
        self.adv_level = None
        self.adv_role_id = None
        
        await interaction.response.edit_message(content="⚠️ **Configuração de Advertência**\nSelecione o membro e o nível da ADV abaixo:", view=self)
        
    async def adv_callback(self, interaction: discord.Interaction):
        if self.adv_select.values[0] == "none":
            return await interaction.response.defer()
        self.adv_role_id = int(self.adv_select.values[0])
        self.adv_level = next((opt.label for opt in self.adv_select.options if opt.value == self.adv_select.values[0]), "Advertência")
        await interaction.response.defer()

    @discord.ui.button(label='Continuar', style=discord.ButtonStyle.success, row=2)
    async def continue_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not self.target_member or not self.adv_role_id:
            return await interaction.response.send_message("❌ Por favor, selecione um membro e o tipo de ADV antes de continuar.", ephemeral=True)
            
        required_role = 1545262380286611559
        if not any(r.id == required_role for r in self.target_member.roles):
            return await interaction.response.send_message("❌ O membro selecionado não possui o cargo necessário (Membro) para receber ADV.", ephemeral=True)
            
        await interaction.response.send_modal(AdvModal(self.target_member, self.adv_level, self.adv_role_id))

class ExoModal(ui.Modal):
    def __init__(self, target_member: discord.Member):
        super().__init__(title="Aplicar Exoneração")
        self.target_member = target_member
        
        self.motivo = ui.TextInput(label="Motivo da Exoneração", style=discord.TextStyle.paragraph, required=True)
        self.provas = ui.TextInput(label="Provas (Links)", style=discord.TextStyle.short, required=True)
        
        self.add_item(self.motivo)
        self.add_item(self.provas)

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.guild.get_member(self.target_member.id)
        if not member:
            return await interaction.response.send_message("❌ Membro não encontrado no servidor.", ephemeral=True)

        exo_role_1 = interaction.guild.get_role(1545440113444528210)
        exo_role_2 = interaction.guild.get_role(1545262380286611557)
        roles_to_add = [r for r in [exo_role_1, exo_role_2] if r is not None]
        
        try:
            # Substitui todos os cargos pelos novos cargos de exoneração (o Discord sempre mantém o @everyone)
            await member.edit(roles=roles_to_add, reason=f"Exoneração aplicada por {interaction.user}")
        except Exception as e:
            print(f"Erro ao exonerar: {e}")
            return await interaction.response.send_message(f"❌ Erro ao modificar os cargos. Verifique se meu cargo está acima de todos do membro! (Erro: {e})", ephemeral=True)
                
        desc = (
            f"👤 **EXONERADO:** {self.target_member.mention} (`{self.target_member.id}`)\n"
            f"📋 **MOTIVO:** {self.motivo.value}\n"
            f"🔗 **PROVA:** {self.provas.value}\n"
            f"🛡️ **RESPONSÁVEL:** {interaction.user.mention}"
        )
        
        embed = discord.Embed(
            title="",
            description=desc,
            color=0x992d22
        )
        avatar_url = self.target_member.display_avatar.url if self.target_member.display_avatar else None
        embed.set_author(name="🚪 SISTEMA DE PUNIÇÕES - EXONERAÇÃO", icon_url=avatar_url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
        embed.set_footer(text="UNIMED DRP - Departamento Pessoal")
        
        log_channel = interaction.guild.get_channel(1545436905775046666)
        if log_channel:
            await log_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Exoneração aplicada com sucesso a {self.target_member.display_name} e registrada no canal {log_channel.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Exoneração aplicada, mas o canal de logs não foi encontrado.", ephemeral=True)

class ExoSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.target_member = None
        
        self.user_select = ui.UserSelect(placeholder="Selecione o membro para exonerar", min_values=1, max_values=1)
        self.user_select.callback = self.user_callback
        self.add_item(self.user_select)
        
    async def user_callback(self, interaction: discord.Interaction):
        self.target_member = self.user_select.values[0]
        await interaction.response.defer()

    @discord.ui.button(label='Continuar', style=discord.ButtonStyle.success, row=1)
    async def continue_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not self.target_member:
            return await interaction.response.send_message("❌ Por favor, selecione um membro antes de continuar.", ephemeral=True)
            
        required_role = 1545262380286611559
        if not any(r.id == required_role for r in self.target_member.roles):
            return await interaction.response.send_message("❌ O membro selecionado não possui o cargo necessário (Membro) para ser exonerado.", ephemeral=True)
            
        await interaction.response.send_modal(ExoModal(self.target_member))

HIERARQUIA = [
    (1545262380286611561, "Estágiario"),
    (1545262380286611563, "Socorrista"),
    (1545262380286611564, "Auxiliar De Enfermagem"),
    (1545262380286611565, "Técnico Em Enfermagem"),
    (1545262380286611566, "Enfermeiro"),
    (1545262380299067462, "Auxiliar Médico"),
    (1545262380299067464, "Médico"),
    (1545262380299067465, "Coordenador Médico"),
    (1545262380299067466, "Coordenador De Enfermagem"),
    (1545262380299067467, "Coordenador Geral"),
    (1545262380299067468, "Gerente Médico (Tst)"),
    (1545262380299067469, "Gerente Médico"),
    (1545262380299067471, "Administração"),
    (1545262380307451964, "Vice Diretor (Teste)"),
    (1545262380307451965, "Vice Diretor"),
    (1545262380307451966, "Diretor"),
    (1545262380307451968, "Co Fundador"),
    (1545262380307451969, "Founder")
]

class UpModal(ui.Modal):
    def __init__(self, target_member: discord.Member, old_role_id: int, new_role_id: int, new_role_name: str):
        super().__init__(title="Aplicar Upamento")
        self.target_member = target_member
        self.old_role_id = old_role_id
        self.new_role_id = new_role_id
        self.new_role_name = new_role_name
        
        self.motivo = ui.TextInput(label="Motivo do Upamento", style=discord.TextStyle.paragraph, required=True)
        
        self.add_item(self.motivo)

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.guild.get_member(self.target_member.id)
        if not member:
            return await interaction.response.send_message("❌ Membro não encontrado.", ephemeral=True)

        new_role = interaction.guild.get_role(self.new_role_id)
        
        hierarquia_ids = [rid for rid, name in HIERARQUIA]
        roles_to_keep = [r for r in member.roles if r.id not in hierarquia_ids]
        
        if new_role:
            roles_to_keep.append(new_role)
            
        try:
            await member.edit(roles=roles_to_keep, reason=f"Upamento feito por {interaction.user}")
        except Exception as e:
            return await interaction.response.send_message(f"❌ Erro ao modificar cargos. Verifique a hierarquia do bot! (Erro: {e})", ephemeral=True)
            
        old_role_mention = f"<@&{self.old_role_id}>" if self.old_role_id else "Nenhum/Indefinido"
        
        desc = (
            f"👤 **MEMBRO:** {self.target_member.mention} (`{self.target_member.id}`)\n"
            f"📉 **CARGO ANTIGO:** {old_role_mention}\n"
            f"📈 **NOVO CARGO:** <@&{self.new_role_id}>\n"
            f"📋 **MOTIVO:** {self.motivo.value}\n"
            f"🛡️ **RESPONSÁVEL:** {interaction.user.mention}"
        )
        
        embed = discord.Embed(title="", description=desc, color=0x2ecc71)
        avatar_url = self.target_member.display_avatar.url if self.target_member.display_avatar else None
        embed.set_author(name="📈 SISTEMA DE CARREIRA - UPAMENTO", icon_url=avatar_url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png")
        embed.set_footer(text="UNIMED DRP - Departamento Pessoal")
        
        log_channel = interaction.guild.get_channel(1545436583501758586)
        if log_channel:
            await log_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Upamento para **{self.new_role_name}** aplicado e registrado em {log_channel.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Upamento aplicado, mas o canal de logs não foi encontrado.", ephemeral=True)

class UpSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.target_member = None
        self.old_role_id = None
        self.new_role_id = None
        self.new_role_name = None
        
        self.user_select = ui.UserSelect(placeholder="Selecione o membro", min_values=1, max_values=1)
        self.user_select.callback = self.user_callback
        self.add_item(self.user_select)
        
        self.role_select = ui.Select(placeholder="Aguardando seleção do membro...", min_values=1, max_values=1, disabled=True, options=[discord.SelectOption(label="...", value="none")])
        self.role_select.callback = self.role_callback
        self.add_item(self.role_select)
        
    async def user_callback(self, interaction: discord.Interaction):
        self.target_member = self.user_select.values[0]
        member = interaction.guild.get_member(self.target_member.id)
        if not member:
            return await interaction.response.defer()
            
        staff = interaction.user
        staff_level = -1
        for i, (rid, name) in enumerate(HIERARQUIA):
            if any(r.id == rid for r in staff.roles):
                staff_level = max(staff_level, i)
                
        target_level = -1
        target_current_role_id = None
        for i, (rid, name) in enumerate(HIERARQUIA):
            if any(r.id == rid for r in member.roles):
                target_level = max(target_level, i)
                target_current_role_id = rid
                
        if staff_level <= target_level and staff_level != -1:
            self.role_select.options = [discord.SelectOption(label="Bloqueado: Patente igual/superior", value="none")]
            self.role_select.disabled = True
            for child in self.children:
                if isinstance(child, discord.ui.Button): child.disabled = True
            return await interaction.response.edit_message(content="❌ Você não tem permissão para promover esse membro (patente dele é igual ou maior que a sua).", view=self)
            
        options = []
        for i, (rid, name) in enumerate(HIERARQUIA):
            # The staff can only promote to roles BELOW their highest role, unless they are Founder (top).
            if i > target_level and i < staff_level:
                options.append(discord.SelectOption(label=name, value=str(rid)))
                
        if not options:
            self.role_select.options = [discord.SelectOption(label="Nenhum cargo disponível", value="none")]
            self.role_select.disabled = True
            for child in self.children:
                if isinstance(child, discord.ui.Button): child.disabled = True
            return await interaction.response.edit_message(content="❌ Não há cargos disponíveis para você promover este membro.", view=self)
            
        self.role_select.options = options
        self.role_select.disabled = False
        self.role_select.placeholder = "Selecione a nova patente"
        self.old_role_id = target_current_role_id
        
        for child in self.children:
            if isinstance(child, discord.ui.Button): child.disabled = False
            
        await interaction.response.edit_message(content="📈 **Configuração de Upamento**\nMembro selecionado. Agora escolha a patente:", view=self)

    async def role_callback(self, interaction: discord.Interaction):
        if self.role_select.values[0] == "none": return await interaction.response.defer()
        self.new_role_id = int(self.role_select.values[0])
        self.new_role_name = next((opt.label for opt in self.role_select.options if opt.value == self.role_select.values[0]), "Desconhecido")
        await interaction.response.defer()

    @discord.ui.button(label='Continuar', style=discord.ButtonStyle.success, row=2)
    async def continue_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not self.target_member or not self.new_role_id:
            return await interaction.response.send_message("❌ Selecione o membro e o novo cargo.", ephemeral=True)
        await interaction.response.send_modal(UpModal(self.target_member, self.old_role_id, self.new_role_id, self.new_role_name))

class RebModal(ui.Modal):
    def __init__(self, target_member: discord.Member, old_role_id: int, new_role_id: int, new_role_name: str):
        super().__init__(title="Aplicar Rebaixamento")
        self.target_member = target_member
        self.old_role_id = old_role_id
        self.new_role_id = new_role_id
        self.new_role_name = new_role_name
        
        self.motivo = ui.TextInput(label="Motivo do Rebaixamento", style=discord.TextStyle.paragraph, required=True)
        self.provas = ui.TextInput(label="Provas (Links)", style=discord.TextStyle.short, required=True)
        
        self.add_item(self.motivo)
        self.add_item(self.provas)

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.guild.get_member(self.target_member.id)
        if not member:
            return await interaction.response.send_message("❌ Membro não encontrado.", ephemeral=True)

        new_role = interaction.guild.get_role(self.new_role_id)
        
        hierarquia_ids = [rid for rid, name in HIERARQUIA]
        roles_to_keep = [r for r in member.roles if r.id not in hierarquia_ids]
        
        if new_role:
            roles_to_keep.append(new_role)
            
        try:
            await member.edit(roles=roles_to_keep, reason=f"Rebaixamento feito por {interaction.user}")
        except Exception as e:
            return await interaction.response.send_message(f"❌ Erro ao modificar cargos. (Erro: {e})", ephemeral=True)
            
        old_role_mention = f"<@&{self.old_role_id}>" if self.old_role_id else "Nenhum/Indefinido"
        
        desc = (
            f"👤 **MEMBRO:** {self.target_member.mention} (`{self.target_member.id}`)\n"
            f"📉 **CARGO ANTIGO:** {old_role_mention}\n"
            f"🔻 **NOVO CARGO:** <@&{self.new_role_id}>\n"
            f"📋 **MOTIVO:** {self.motivo.value}\n"
            f"🔗 **PROVA:** {self.provas.value}\n"
            f"🛡️ **RESPONSÁVEL:** {interaction.user.mention}"
        )
        
        embed = discord.Embed(title="", description=desc, color=0x95a5a6)
        avatar_url = self.target_member.display_avatar.url if self.target_member.display_avatar else None
        embed.set_author(name="🔻 SISTEMA DE CARREIRA - REBAIXAMENTO", icon_url=avatar_url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png")
        embed.set_footer(text="UNIMED DRP - Departamento Pessoal")
        
        log_channel = interaction.guild.get_channel(1545436632860074115)
        if log_channel:
            await log_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Rebaixamento para **{self.new_role_name}** aplicado e registrado em {log_channel.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Rebaixamento aplicado, mas o canal de logs não foi encontrado.", ephemeral=True)

class RebSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.target_member = None
        self.old_role_id = None
        self.new_role_id = None
        self.new_role_name = None
        
        self.user_select = ui.UserSelect(placeholder="Selecione o membro", min_values=1, max_values=1)
        self.user_select.callback = self.user_callback
        self.add_item(self.user_select)
        
        self.role_select = ui.Select(placeholder="Aguardando seleção do membro...", min_values=1, max_values=1, disabled=True, options=[discord.SelectOption(label="...", value="none")])
        self.role_select.callback = self.role_callback
        self.add_item(self.role_select)
        
    async def user_callback(self, interaction: discord.Interaction):
        self.target_member = self.user_select.values[0]
        member = interaction.guild.get_member(self.target_member.id)
        if not member:
            return await interaction.response.defer()
            
        staff = interaction.user
        staff_level = -1
        for i, (rid, name) in enumerate(HIERARQUIA):
            if any(r.id == rid for r in staff.roles):
                staff_level = max(staff_level, i)
                
        target_level = -1
        target_current_role_id = None
        for i, (rid, name) in enumerate(HIERARQUIA):
            if any(r.id == rid for r in member.roles):
                target_level = max(target_level, i)
                target_current_role_id = rid
                
        if staff_level <= target_level and staff_level != -1:
            self.role_select.options = [discord.SelectOption(label="Bloqueado: Patente igual/superior", value="none")]
            self.role_select.disabled = True
            for child in self.children:
                if isinstance(child, discord.ui.Button): child.disabled = True
            return await interaction.response.edit_message(content="❌ Você não tem permissão para rebaixar esse membro (patente dele é igual ou maior que a sua).", view=self)
            
        options = []
        # Mostrar apenas cargos abaixo do alvo
        for i in range(len(HIERARQUIA)-1, -1, -1):
            rid, name = HIERARQUIA[i]
            if i < target_level:
                options.append(discord.SelectOption(label=name, value=str(rid)))
                
        if not options:
            self.role_select.options = [discord.SelectOption(label="Nenhum cargo disponível", value="none")]
            self.role_select.disabled = True
            for child in self.children:
                if isinstance(child, discord.ui.Button): child.disabled = True
            return await interaction.response.edit_message(content="❌ Não há patentes menores para rebaixar este membro (já está na menor patente).", view=self)
            
        self.role_select.options = options
        self.role_select.disabled = False
        self.role_select.placeholder = "Selecione a patente de rebaixamento"
        self.old_role_id = target_current_role_id
        
        for child in self.children:
            if isinstance(child, discord.ui.Button): child.disabled = False
            
        await interaction.response.edit_message(content="🔻 **Configuração de Rebaixamento**\nMembro selecionado. Escolha a patente inferior:", view=self)

    async def role_callback(self, interaction: discord.Interaction):
        if self.role_select.values[0] == "none": return await interaction.response.defer()
        self.new_role_id = int(self.role_select.values[0])
        self.new_role_name = next((opt.label for opt in self.role_select.options if opt.value == self.role_select.values[0]), "Desconhecido")
        await interaction.response.defer()

    @discord.ui.button(label='Continuar', style=discord.ButtonStyle.danger, row=2)
    async def continue_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not self.target_member or not self.new_role_id:
            return await interaction.response.send_message("❌ Selecione o membro e o novo cargo.", ephemeral=True)
        await interaction.response.send_modal(RebModal(self.target_member, self.old_role_id, self.new_role_id, self.new_role_name))

class AdminActionModal(ui.Modal):
    def __init__(self, action_name: str, color: int, log_channel_id: int):
        super().__init__(title=f"Ação: {action_name}")
        self.action_name = action_name
        self.color = color
        self.log_channel_id = log_channel_id
        
        self.user_id = ui.TextInput(label="ID do Membro", required=True)
        self.motivo = ui.TextInput(label="Motivo / Justificativa", style=discord.TextStyle.paragraph, required=True)
        
        self.add_item(self.user_id)
        self.add_item(self.motivo)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.user_id.value.strip())
        except ValueError:
            return await interaction.response.send_message("❌ ID inválido.", ephemeral=True)
            
        embed = discord.Embed(
            title=f"📋 Registro de {self.action_name}",
            color=self.color
        )
        embed.add_field(name="Membro Afetado", value=f"<@{uid}> (`{uid}`)", inline=False)
        embed.add_field(name="Responsável", value=f"{interaction.user.mention}", inline=False)
        embed.add_field(name="Motivo", value=self.motivo.value, inline=False)
        
        log_channel = interaction.guild.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Ação de {self.action_name} registrada com sucesso no canal {log_channel.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ Ação de {self.action_name} realizada, mas o canal de logs não foi encontrado.", ephemeral=True)


class PainelAdminView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='ADVERTÊNCIA', style=discord.ButtonStyle.danger, custom_id='adm_adv_btn')
    async def adv_btn(self, interaction: discord.Interaction, button: ui.Button):
        role_id = 1545437764391272550
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not any(r.id == role_id for r in member.roles):
            embed_erro = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para aplicar Advertência.", color=0xff0000)
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)
        await interaction.response.send_message("⚠️ **Configuração de Advertência**\nSelecione o membro e o nível da ADV abaixo:", view=AdvSelectView(), ephemeral=True)

    @discord.ui.button(label='EXONERAÇÃO', style=discord.ButtonStyle.danger, custom_id='adm_exo_btn')
    async def exo_btn(self, interaction: discord.Interaction, button: ui.Button):
        role_id = 1545437734599139399
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not any(r.id == role_id for r in member.roles):
            embed_erro = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para aplicar Exoneração.", color=0xff0000)
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)
        await interaction.response.send_message("🚪 **Configuração de Exoneração**\nSelecione o membro que será exonerado:", view=ExoSelectView(), ephemeral=True)

    @discord.ui.button(label='UPAMENTO', style=discord.ButtonStyle.success, custom_id='adm_up_btn')
    async def up_btn(self, interaction: discord.Interaction, button: ui.Button):
        role_id = 1545437621357125672
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not any(r.id == role_id for r in member.roles):
            embed_erro = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para realizar Upamentos.", color=0xff0000)
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)
        await interaction.response.send_message("📈 **Configuração de Upamento**\nSelecione o membro e o sistema carregará as patentes disponíveis:", view=UpSelectView(), ephemeral=True)

    @discord.ui.button(label='REBAIXAMENTO', style=discord.ButtonStyle.secondary, custom_id='adm_reb_btn')
    async def reb_btn(self, interaction: discord.Interaction, button: ui.Button):
        role_id = 1545437694996516994
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not any(r.id == role_id for r in member.roles):
            embed_erro = discord.Embed(title="❌ Acesso Negado", description="Você não tem permissão para realizar Rebaixamentos.", color=0xff0000)
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)
        await interaction.response.send_message("🔻 **Configuração de Rebaixamento**\nSelecione o membro e o sistema carregará as patentes inferiores:", view=RebSelectView(), ephemeral=True)

class DeleteMessageView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        
    @discord.ui.button(label="Fechar Aviso", style=discord.ButtonStyle.secondary, emoji="🗑️")
    async def fechar_btn(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Apenas quem recebeu o aviso pode fechá-lo.", ephemeral=True)
        try:
            await interaction.message.delete()
        except:
            pass

class TicketAddMemberModal(ui.Modal):
    def __init__(self, ticket_channel):
        super().__init__(title="Adicionar Membro ao Ticket")
        self.ticket_channel = ticket_channel
        self.user_id_input = ui.TextInput(label="ID do Usuário", style=discord.TextStyle.short, required=True)
        self.add_item(self.user_id_input)
        
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id_input.value.strip())
            member = interaction.guild.get_member(user_id)
            if not member:
                return await interaction.response.send_message("❌ Membro não encontrado no servidor.", ephemeral=True)
                
            await self.ticket_channel.set_permissions(member, read_messages=True, send_messages=True, attach_files=True, embed_links=True)
            await interaction.response.send_message(f"✅ {member.mention} foi adicionado ao ticket por {interaction.user.mention}.")
            
            # Atualizar Log
            if MONGO_URI:
                ticket_data = await db.tickets.find_one({"channel_id": self.ticket_channel.id})
                if ticket_data:
                    log_channel = interaction.guild.get_channel(1545461015691395122)
                    if log_channel:
                        try:
                            log_msg = await log_channel.fetch_message(ticket_data["log_msg_id"])
                            embed = log_msg.embeds[0]
                            embed.add_field(name="👤 Membro adicionado", value=member.mention, inline=False)
                            await log_msg.edit(embed=embed)
                        except:
                            pass
        except ValueError:
            await interaction.response.send_message("❌ ID inválido. Por favor insira apenas números.", ephemeral=True)

class TicketPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    async def check_staff(self, interaction: discord.Interaction):
        staff_role_id = 1545459826237382747
        if not any(r.id == staff_role_id for r in interaction.user.roles):
            await interaction.response.send_message("❌ Você não tem permissão para usar as funções do painel.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Assumir Atendimento", style=discord.ButtonStyle.success, emoji="🙋", custom_id="ticket_assume_btn")
    async def assume_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_staff(interaction): return
        
        topic = interaction.channel.topic or ""
        if "Assumed:0" not in topic:
            return await interaction.response.send_message("❌ Este ticket já foi assumido.", ephemeral=True)
            
        new_topic = topic.replace("Assumed:0", f"Assumed:{interaction.user.id}")
        await interaction.channel.edit(topic=new_topic)
        
        await interaction.channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        
        await interaction.response.send_message(f"👨‍💻 **Atendimento assumido por:** {interaction.user.mention}")
        
        # Atualizar Log e BD
        if MONGO_URI:
            ticket_data = await db.tickets.find_one({"channel_id": interaction.channel.id})
            if ticket_data:
                await db.tickets.update_one({"channel_id": interaction.channel.id}, {"$set": {"assumed_by": interaction.user.id, "status": "Em atendimento"}})
                log_channel = interaction.guild.get_channel(1545461015691395122)
                if log_channel:
                    try:
                        log_msg = await log_channel.fetch_message(ticket_data["log_msg_id"])
                        embed = log_msg.embeds[0]
                        
                        desc_lines = embed.description.split("\n")
                        for i, line in enumerate(desc_lines):
                            if line.startswith("🟡 Status:"):
                                desc_lines[i] = "🟢 Status: Em atendimento"
                            elif line.startswith("🙋 Responsável:"):
                                desc_lines[i] = f"🙋 Responsável: {interaction.user.mention}"
                                
                        embed.description = "\n".join(desc_lines)
                        embed.color = 0x2ecc71
                        await log_msg.edit(embed=embed)
                    except Exception as e:
                        print("Erro edit log assume", e)
                        pass

    @discord.ui.button(label="Notificar", style=discord.ButtonStyle.primary, emoji="📢", custom_id="ticket_notify_btn")
    async def notify_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_staff(interaction): return
        
        topic = interaction.channel.topic or ""
        opener_id = None
        for part in topic.split(" | "):
            if part.startswith("Opener:"):
                opener_id = int(part.split(':')[1])
                
        opener = interaction.guild.get_member(opener_id) if opener_id else None
        
        msg = await interaction.channel.send(content=f"🔔 {opener.mention if opener else 'Usuário'}, a equipe da UNIMED está aguardando seu retorno neste ticket!")
        await interaction.response.send_message("✅ Notificação enviada.", ephemeral=True)
        
        # Atualizar log
        if MONGO_URI:
            ticket_data = await db.tickets.find_one({"channel_id": interaction.channel.id})
            if ticket_data:
                log_channel = interaction.guild.get_channel(1545461015691395122)
                if log_channel:
                    try:
                        log_msg = await log_channel.fetch_message(ticket_data["log_msg_id"])
                        embed = log_msg.embeds[0]
                        import datetime
                        time_str = datetime.datetime.now().strftime("%d/%m %H:%M")
                        embed.add_field(name="📢 Notificação enviada", value=f"Por {interaction.user.mention} às {time_str}", inline=False)
                        await log_msg.edit(embed=embed)
                    except:
                        pass

    @discord.ui.button(label="Adicionar Membro", style=discord.ButtonStyle.secondary, emoji="➕", custom_id="ticket_add_btn")
    async def add_btn(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_staff(interaction): return
        await interaction.response.send_modal(TicketAddMemberModal(interaction.channel))

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close_btn")
    async def close_btn(self, interaction: discord.Interaction, button: ui.Button):
        topic = interaction.channel.topic or ""
        opener_id = None
        for part in topic.split(" | "):
            if part.startswith("Opener:"):
                opener_id = int(part.split(':')[1])
                
        staff_role_id = 1545459826237382747
        is_staff = any(r.id == staff_role_id for r in interaction.user.roles)
        
        if interaction.user.id != opener_id and not is_staff:
            return await interaction.response.send_message("❌ Apenas o criador do ticket ou a equipe podem fechá-lo.", ephemeral=True)
            
        if MONGO_URI:
            ticket_data = await db.tickets.find_one({"channel_id": interaction.channel.id})
            if ticket_data and ticket_data.get("status") == "Encerrado":
                return await interaction.response.send_message("⚠️ Este ticket já está sendo encerrado.", ephemeral=True)
            
        await interaction.response.defer()
        
        for item in self.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self)
        except:
            pass
        
        import io
        messages = [message async for message in interaction.channel.history(limit=2000, oldest_first=True)]
        transcript_lines = []
        for msg in messages:
            time_str = msg.created_at.strftime("%d/%m/%Y %H:%M:%S")
            transcript_lines.append(f"[{time_str}] {msg.author.name}: {msg.clean_content}")
            if msg.attachments:
                for att in msg.attachments:
                    transcript_lines.append(f"    [Anexo] {att.url}")
                    
        transcript_text = "\n".join(transcript_lines)
        transcript_file = discord.File(io.BytesIO(transcript_text.encode('utf-8')), filename=f"{interaction.channel.name}.txt")

        # Atualizar BD e Log Final
        if MONGO_URI:
            ticket_data = await db.tickets.find_one({"channel_id": interaction.channel.id})
            if ticket_data:
                await db.tickets.update_one({"channel_id": interaction.channel.id}, {"$set": {"status": "Encerrado"}})
                log_channel = interaction.guild.get_channel(1545461015691395122)
                
                opener_user = f"<@{ticket_data['opener_id']}>" if ticket_data.get('opener_id') else "Desconhecido"
                resp_user = f"<@{ticket_data['assumed_by']}>" if ticket_data.get('assumed_by') else "Ninguém"
                
                if log_channel:
                    try:
                        log_msg = await log_channel.fetch_message(ticket_data["log_msg_id"])
                        embed = log_msg.embeds[0]
                        embed.title = "🎫 Ticket Encerrado"
                        embed.color = 0xff0000
                        
                        desc_lines = embed.description.split("\n")
                        for i, line in enumerate(desc_lines):
                            if line.startswith("🟢 Status:") or line.startswith("🟡 Status:"):
                                desc_lines[i] = "🔴 Status: Encerrado"
                                
                        import datetime
                        time_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                        desc_lines.append(f"🔒 Encerrado por: {interaction.user.mention}")
                        desc_lines.append(f"🕐 Encerrado em: {time_str}")
                        
                        embed.description = "\n".join(desc_lines)
                        await log_msg.edit(embed=embed, attachments=[])
                    except:
                        pass
                
                transcript_channel = interaction.guild.get_channel(1545458900613079130)
                if transcript_channel:
                    import datetime
                    time_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    trans_embed = discord.Embed(title="📄 Transcript do Ticket", color=0x2b2d31)
                    trans_embed.add_field(name="👤 Usuário", value=opener_user, inline=True)
                    trans_embed.add_field(name="🙋 Responsável", value=resp_user, inline=True)
                    trans_embed.add_field(name="🕐 Data/Hora", value=time_str, inline=False)
                    await transcript_channel.send(embed=trans_embed, file=transcript_file)
        
        await interaction.followup.send("🔒 Encerrando ticket...", ephemeral=False)
        import asyncio
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete()
        except:
            pass

class SupportSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Dúvida", emoji="❓", description="Tire suas dúvidas", value="duvida"),
            discord.SelectOption(label="Denúncia", emoji="🚨", description="Faça uma denúncia", value="denuncia"),
            discord.SelectOption(label="Recorrer Advertência", emoji="⚠️", description="Recorrer de uma ADV recebida", value="recorrer"),
            discord.SelectOption(label="Patrocínio", emoji="💎", description="Assuntos comerciais / patrocínio", value="patrocinio")
        ]
        super().__init__(placeholder="Selecione a categoria desejada", min_values=1, max_values=1, options=options, custom_id="support_select")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        user = interaction.user
        value = self.values[0]
        
        prefixes = {
            "duvida": "❓・dúvida",
            "denuncia": "🚨・denúncia",
            "recorrer": "⚠️・recorrer",
            "patrocinio": "💎・patrocínio"
        }
        
        channel_name = f"{prefixes[value]}-{user.name}"
        
        existing_channel = discord.utils.find(lambda c: user.name.lower() in c.name.lower() and prefixes[value].split("・")[1].lower() in c.name.lower(), guild.text_channels)
        if existing_channel:
            return await interaction.followup.send(f"❌ Você já possui um ticket desta categoria aberto: {existing_channel.mention}", ephemeral=True)
            
        staff_role = guild.get_role(1545459826237382747)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True)
        }
        if staff_role:
            # Equipe vê, mas ainda não pode enviar (só depois de assumir, exceto se for interceptado no on_message)
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        try:
            category = guild.get_channel(1545456154442731600)
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Opener:{user.id} | Categoria:{value.capitalize()} | Assumed:0",
                reason=f"Ticket aberto por {user.name}"
            )
        except Exception as e:
            return await interaction.followup.send(f"❌ Erro ao criar o ticket. Verifique as permissões do bot. ({e})", ephemeral=True)
            
        # 1. Enviar instantaneamente o painel no canal do ticket
        embed = discord.Embed(
            title=f"Ticket - {user.display_name}",
            description=f"Bem-vindo(a) ao suporte da **UNIMED DRP**.\nCategoria: **{value.capitalize()}**.\n\nNossa equipe foi notificada e irá te atender em breve.\nAguarde um membro da equipe assumir o atendimento.",
            color=0x3498db
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png")
        
        await ticket_channel.send(content=f"{user.mention}", embed=embed, view=TicketPanelView())
        await interaction.followup.send(f"✅ Seu ticket foi aberto com sucesso: {ticket_channel.mention}", ephemeral=True)
        
        # Resetar o select menu para o estado original
        try:
            await interaction.message.edit(view=SupportView())
        except:
            pass

        # 2. Registrar log no canal e no MongoDB em segundo plano (sem atrasar a exibição)
        async def registrar_log_background(ch_id, uid, cat_val):
            if not MONGO_URI: return
            log_channel = guild.get_channel(1545461015691395122)
            if log_channel:
                import datetime
                time_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                log_embed = discord.Embed(
                    title="🎫 Ticket Criado",
                    description=f"👤 Usuário: <@{uid}>\n📁 Categoria: {cat_val.capitalize()}\n🕐 Aberto em: {time_str}\n🟡 Status: Aguardando atendimento\n🙋 Responsável: Ninguém",
                    color=0xf1c40f
                )
                try:
                    log_msg = await log_channel.send(embed=log_embed)
                    await db.tickets.insert_one({
                        "channel_id": ch_id,
                        "log_msg_id": log_msg.id,
                        "opener_id": uid,
                        "assumed_by": None,
                        "status": "Aguardando",
                        "category": cat_val
                    })
                except Exception as e:
                    print("Erro log db background:", e)

        asyncio.create_task(registrar_log_background(ticket_channel.id, user.id, value))

class SupportView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SupportSelect())

class UnimedBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        self.add_view(RecruitmentView())
        self.add_view(RegistrationView())
        self.add_view(TagRequestView())
        self.add_view(AssumirTagView())
        self.add_view(AtendimentoTagView())
        self.add_view(BatePontoView())
        self.add_view(PainelAdminView())
        self.add_view(SupportView())
        self.add_view(TicketPanelView())
        self.rank_mensal.start()
        self.verificar_testes_expirados.start()

    @tasks.loop(minutes=60)
    async def rank_mensal(self):
        import datetime
        agora = datetime.datetime.now()
        if agora.day == 30 and agora.hour == 12:
            if not MONGO_URI: return
            channel = self.get_channel(1545433966427766945)
            if not channel: return
            
            guild = channel.guild
            if not guild: return
            
            # (Mantendo o código intacto do rank_mensal)
            cursor = db.bate_ponto_horas.find({"guild_id": guild.id}).sort("total_segundos", -1)
            docs = await cursor.to_list(length=20)
            
            cargo_id = 1545262380286611559
            cargo = guild.get_role(cargo_id)
            if not cargo: return
            
            all_users = await db.bate_ponto_horas.find({}).to_list(length=1000)
            
            rank_list = []
            for u in all_users:
                member = guild.get_member(u["user_id"])
                if member and cargo in member.roles:
                    rank_list.append((member, u.get("total_seconds", 0)))
                    
            rank_list.sort(key=lambda x: x[1], reverse=True)
            
            desc = ""
            for idx, (mem, secs) in enumerate(rank_list[:20], 1):
                horas, remainder = divmod(secs, 3600)
                minutos, _ = divmod(remainder, 60)
                desc += f"**{idx}º** | {mem.mention} - `{horas:02d}h {minutos:02d}m`\n"
                
            if not desc:
                desc = "Nenhum membro possui horas registradas."
                
            embed = discord.Embed(
                title="🏆 Ranking Mensal de Horas (UNIMED)",
                description=desc,
                color=0xf1c40f
            )
            embed.set_footer(text=f"Fechamento: {agora.strftime('%m/%Y')}")
            
            await channel.send(embed=embed)
            
            # EXO automático: membros com 0 horas
            exo_log_channel = self.get_channel(1545436905775046666)
            exo_role_1 = guild.get_role(1545440113444528210)
            exo_role_2 = guild.get_role(1545262380286611557)
            roles_to_add = [r for r in [exo_role_1, exo_role_2] if r is not None]
            
            # Pegar todos os membros com o cargo de membro ativo
            membros_com_cargo = [m for m in guild.members if cargo in m.roles]
            # Pegar IDs que têm registro de horas (mesmo que seja 0 mas estão no banco)
            ids_com_registro = {u["user_id"]: u.get("total_segundos", u.get("total_seconds", 0)) for u in all_users}
            
            exonerados = []
            for member in membros_com_cargo:
                horas_membro = ids_com_registro.get(member.id, 0)
                if horas_membro == 0:
                    try:
                        await member.edit(roles=roles_to_add, reason="EXO automático — 0 horas no fechamento mensal")
                        exonerados.append(member)
                    except Exception as e:
                        print(f"Erro ao exonerar {member}: {e}")
                        
            if exonerados and exo_log_channel:
                desc_exo = "\n".join([f"• {m.mention} (`{m.id}`)" for m in exonerados])
                embed_exo = discord.Embed(
                    title="🔴 EXONERAÇÕES AUTOMÁTICAS — FECHAMENTO MENSAL",
                    description=(
                        f"Os seguintes membros foram **exonerados automaticamente** por não registrarem "
                        f"**nenhuma hora de Bate Ponto** durante o mês de `{agora.strftime('%m/%Y')}`:\n\n"
                        f"{desc_exo}"
                    ),
                    color=0xff0000
                )
                embed_exo.set_footer(text=f"Fechamento automático: {agora.strftime('%d/%m/%Y %H:%M')}")
                await exo_log_channel.send(embed=embed_exo)
            
            # Zerar horas de todos para o próximo mês
            await db.bate_ponto_horas.update_many({}, {"$set": {"total_segundos": 0, "total_seconds": 0}})

    @rank_mensal.before_loop
    async def before_rank_mensal(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=1)
    async def verificar_testes_expirados(self):
        category_id = 1545278162173296730
        category = self.get_channel(category_id)
        if not category:
            return
        agora = discord.utils.utcnow()
        for channel in category.text_channels:
            if channel.name.startswith("teste-"):
                segundos_aberto = (agora - channel.created_at).total_seconds()
                if segundos_aberto >= 600:  # 10 minutos
                    try:
                        embed_timeout = discord.Embed(
                            title="⏰ TEMPO ESGOTADO!",
                            description="Os 10 minutos para concluir o teste se esgotaram.\nEste canal será fechado agora.",
                            color=0xff0000
                        )
                        await channel.send(embed=embed_timeout)
                        await asyncio.sleep(4)
                        await channel.delete()
                    except Exception as e:
                        print(f"Erro ao fechar canal expirado {channel.name}: {e}")

    @verificar_testes_expirados.before_loop
    async def before_verificar_testes_expirados(self):
        await self.wait_until_ready()

    async def on_message(self, message):
        if message.author.bot:
            return
            
        staff_role_id = 1545459826237382747
        if isinstance(message.channel, discord.TextChannel):
            topic = message.channel.topic or ""
            if "Opener:" in topic and "Categoria:" in topic:
                is_staff = any(r.id == staff_role_id for r in message.author.roles)
                
                opener_id = None
                assumed_by = None
                for part in topic.split(" | "):
                    if part.startswith("Opener:"):
                        opener_id = part.split(":")[1]
                    elif part.startswith("Assumed:"):
                        assumed_by = part.split(":")[1]
                
                if is_staff and assumed_by != str(message.author.id) and str(message.author.id) != opener_id:
                    await message.delete()
                    
                    embed_aviso = discord.Embed(
                        title="Acesso Negado",
                        description=f"❌ Você não pode enviar mensagens neste ticket ({message.channel.name}) pois não assumiu o atendimento.",
                        color=0xff0000
                    )
                    await message.channel.send(content=message.author.mention, embed=embed_aviso, view=DeleteMessageView(message.author.id))
                    
                    # Avisa o dono real na DM (opcional, mantendo o requerimento anterior)
                    try:
                        if assumed_by and assumed_by != "0":
                            real_assumed = self.get_user(int(assumed_by))
                            if real_assumed:
                                await real_assumed.send(f"⚠️ O membro da equipe {message.author.mention} tentou enviar uma mensagem no seu ticket ({message.channel.mention}) sem ter assumido o atendimento.")
                    except:
                        pass
                        
                    return # Stop here for unauthorized staff
                        
                # Filtro Anti-Desrespeito (Aplica-se ao opener e ao staff que assumiu)
                swear_words = ["fdp", "filho da puta", "arrombado", "vsf", "vai se foder", "cuzão", "cuzao", "merda", "bosta", "desgraça", "desgraca", "viado", "puta", "lixo", "corno", "macaco", "otario", "otário", "trouxa"]
                msg_lower = message.content.lower().replace("0", "o").replace("1", "i").replace("3", "e").replace("4", "a").replace("5", "s").replace("@", "a")
                
                for swear in swear_words:
                    if swear in msg_lower:
                        await message.delete()
                        import datetime
                        duration = datetime.timedelta(hours=24)
                        try:
                            await message.author.timeout(duration, reason="Desrespeito à equipe da UNIMED")
                        except Exception as e:
                            print("Erro ao aplicar timeout:", e)
                            
                        await message.channel.send(f"⚠️ {message.author.mention}, você foi silenciado por 24 horas por uso de palavras ofensivas/desrespeitosas.")
                        
                        if MONGO_URI:
                            ticket_data = await db.tickets.find_one({"channel_id": message.channel.id})
                            if ticket_data:
                                log_channel = message.guild.get_channel(1545461015691395122)
                                if log_channel:
                                    try:
                                        log_msg = await log_channel.fetch_message(ticket_data["log_msg_id"])
                                        embed = log_msg.embeds[0]
                                        embed.add_field(
                                            name="⚠️ Ocorrência registrada", 
                                            value=f"👤 Usuário punido: {message.author.mention}\n📋 Motivo: Uso de linguagem ofensiva\n🔨 Punição: 24 horas\n🗣️ Palavra: ||{swear}||", 
                                            inline=False
                                        )
                                        await log_msg.edit(embed=embed)
                                    except:
                                        pass
                        break

        await self.process_commands(message)

bot = UnimedBot()

if MONGO_URI:
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = mongo_client['unimed_bot']
    print("MongoDB configurado!", flush=True)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} conectado com sucesso!', flush=True)

@bot.command()
async def setup_registro(ctx):
    embed = discord.Embed(
        title="", 
        description="Você está prestes a realizar o seu **Registro** para acesso ao servidor da **UNIMED**.\n\n"
                    "📌 **INSTRUÇÕES:**\n"
                    "• Clique no botão azul abaixo para iniciar.\n"
                    "• Preencha com o seu **Nome no Jogo** e o seu **Passaporte (ID)**.\n"
                    "• Seu apelido será alterado automaticamente após o envio.\n\n"
                    "*A dedicação, o respeito e o compromisso começam aqui.*\n*Boa sorte!*",
        color=0x2ecc71
    )
    embed.set_author(name="SISTEMA DE REGISTRO UNIMED", icon_url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
    embed.set_image(url="https://media.discordapp.net/attachments/1293346011691089992/1526567051412508824/content.png?ex=6a9b631b&is=6a9a119b&hm=bb544feeacd842de5bd189b27962b3575c2b498b40d061b481bd2620d58cc8ea&=&format=webp&quality=lossless&width=2048&height=683")
    embed.set_footer(text="Sistema Automatizado por UNIMED DRP")
    
    await ctx.send(embed=embed, view=RegistrationView())
    await ctx.message.delete()

@bot.command()
async def setup_recrutamento(ctx):
    embed = discord.Embed(
        title="", 
        description="Você está prestes a iniciar o processo seletivo para integrar as fileiras da **UNIMED**.\n\n"
                    "📌 **INSTRUÇÕES:**\n"
                    "• Clique no botão verde abaixo para iniciar.\n"
                    "• O teste contém 15 questões de múltipla escolha.\n"
                    "• É necessário acertar no mínimo 60% para ser aprovado.\n"
                    "• Um canal privado será criado automaticamente para você realizar a prova.\n\n"
                    "*A dedicação, o respeito e o compromisso começam aqui.*\n*Boa sorte!*",
        color=0x2ecc71
    )
    embed.set_author(name="SISTEMA DE RECRUTAMENTO UNIMED", icon_url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
    embed.set_image(url="https://media.discordapp.net/attachments/1293346011691089992/1526567051412508824/content.png?ex=6a9b631b&is=6a9a119b&hm=bb544feeacd842de5bd189b27962b3575c2b498b40d061b481bd2620d58cc8ea&=&format=webp&quality=lossless&width=2048&height=683")
    embed.set_footer(text="Sistema Automatizado por UNIMED DRP")
    
    await ctx.send(embed=embed, view=RecruitmentView())
    await ctx.message.delete()

SMALL_CAPS = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
)

@bot.event
async def on_voice_state_update(member, before, after):
    if not MONGO_URI: return
    
    cat_id = 1545262381804818432
    was_in_valid_call = before.channel and before.channel.category_id == cat_id
    is_in_valid_call = after.channel and after.channel.category_id == cat_id
    
    if was_in_valid_call and not is_in_valid_call:
        bp_ativo = await db.bate_ponto.find_one({"user_id": member.id})
        if bp_ativo:
            try:
                embed_aviso = discord.Embed(
                    title="⚠️ Atenção ao Bate Ponto!",
                    description="Você saiu da call de patrulhamento com o ponto aberto!\nVocê tem **2 minutos** para retornar à call ou fechar o ponto no painel. Caso contrário, ele será fechado automaticamente.",
                    color=0xf1c40f
                )
                await member.send(embed=embed_aviso)
            except:
                pass
                
            await asyncio.sleep(120)
            
            bp_ainda_ativo = await db.bate_ponto.find_one({"user_id": member.id})
            if bp_ainda_ativo:
                current_voice = member.voice
                if current_voice and current_voice.channel and current_voice.channel.category_id == cat_id:
                    return
                    
                import datetime
                agora = datetime.datetime.now()
                inicio = bp_ainda_ativo["start_time"]
                diff = agora - inicio
                
                horas, remainder = divmod(int(diff.total_seconds()), 3600)
                minutos, segundos = divmod(remainder, 60)
                total_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                
                if bp_ainda_ativo.get("channel_id") and bp_ainda_ativo.get("message_id"):
                    log_channel = member.guild.get_channel(bp_ainda_ativo["channel_id"])
                    if log_channel:
                        try:
                            msg = await log_channel.fetch_message(bp_ainda_ativo["message_id"])
                            texto_log = (
                                f"<:USER:1545273489378910281> **MEMBRO:** {member.mention}\n"
                                f"<:mas:1545273487139274853> **INÍCIO:** {inicio.strftime('%H:%M')}\n"
                                f"<:bp:1545273485348315156> **TÉRMINO:** {agora.strftime('%H:%M')}\n"
                                f"<:relogio:1545273488514748536> **TOTAL:** {total_str}\n\n"
                                f"⚠️ *Ponto finalizado automaticamente (Não retornou à call)*"
                            )
                            await msg.edit(content=texto_log)
                        except Exception as e:
                            print(f"Erro auto-close: {e}")
                            
                await db.bate_ponto_horas.update_one(
                    {"user_id": member.id},
                    {"$inc": {"total_seconds": int(diff.total_seconds())}},
                    upsert=True
                )
                await db.bate_ponto.delete_one({"user_id": member.id})
                
                try:
                    await member.send("🔒 Seu ponto foi **fechado automaticamente** pois você não retornou à call dentro do tempo limite.")
                except:
                    pass
                
                alert_channel = member.guild.get_channel(1545405516673450134)
                if alert_channel:
                    try:
                        await alert_channel.send(f"⚠️ ALERTA: O membro {member.mention} teve seu ponto finalizado automaticamente. Motivo: Não retornou a call de patrulha")
                    except:
                        pass


@bot.command()
@commands.has_permissions(administrator=True)
async def arruma_canais(ctx):
    mensagem = await ctx.send("⏳ Iniciando a alteração dos nomes dos canais para small caps (isso pode demorar um pouco para não tomar block do Discord)...")
    alterados = 0
    
    for channel in ctx.guild.channels:
        # Converte para minúsculo e depois para small caps
        novo_nome = channel.name.lower().translate(SMALL_CAPS)
        
        # Opcional: muita gente gosta de trocar o "-" por um espaço ou ponto no small caps.
        novo_nome = novo_nome.replace("-", "・")
        
        if novo_nome != channel.name:
            try:
                await channel.edit(name=novo_nome)
                alterados += 1
                await asyncio.sleep(1.5) # Pausa para evitar rate limit do Discord
            except Exception as e:
                print(f"Erro ao renomear {channel.name}: {e}")
                
    await mensagem.edit(content=f"✅ Prontinho! **{alterados}** canais foram formatados com a nova fonte.")
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tag(ctx):
    embed = discord.Embed(
        title="",
        description="Você está prestes a solicitar a sua **Tag In-Game** para finalizar a sua entrada na corporação da **UNIMED**.\n\n"
                    "📌 **INSTRUÇÕES:**\n"
                    "• Clique no botão abaixo para iniciar sua solicitação.\n"
                    "• Apenas membros já aprovados e registrados podem solicitar.\n"
                    "• É permitido solicitar a tag apenas uma vez.\n"
                    "• Após solicitar, aguarde ser atendido por um responsável.\n\n"
                    "*A dedicação, o respeito e o compromisso começam aqui.*\n*Boa sorte!*",
        color=0x2ecc71
    )
    embed.set_author(name="SISTEMA DE SOLICITAÇÃO DE TAG", icon_url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
    embed.set_image(url="https://media.discordapp.net/attachments/1293346011691089992/1526567051412508824/content.png?ex=6a9b631b&is=6a9a119b&hm=bb544feeacd842de5bd189b27962b3575c2b498b40d061b481bd2620d58cc8ea&=&format=webp&quality=lossless&width=2048&height=683")
    embed.set_footer(text="Sistema Automatizado por UNIMED DRP")
    
    await ctx.send(embed=embed, view=TagRequestView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_suporte(ctx):
    embed = discord.Embed(
        title="",
        description="Seja bem-vindo(a) à **Central de Atendimento da UNIMED**.\n\n"
                    "Utilize o menu abaixo para selecionar o departamento que você deseja contatar. "
                    "Um canal privado será criado para que você converse diretamente com nossa equipe.\n\n"
                    "❓ **Dúvida:** Esclareça suas dúvidas gerais.\n"
                    "🚨 **Denúncia:** Reporte infrações de membros da corporação.\n"
                    "⚠️ **Recorrer Advertência:** Abra recurso contra uma punição recebida.\n"
                    "💎 **Patrocínio:** Fale sobre doações e questões comerciais.\n\n"
                    "*Por favor, evite abrir tickets sem necessidade.*",
        color=0x3498db
    )
    embed.set_author(name="CENTRAL DE ATENDIMENTO - SUPORTE", icon_url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png")
    embed.set_image(url="https://media.discordapp.net/attachments/1293346011691089992/1526567051412508824/content.png")
    embed.set_footer(text="Sistema de Tickets Automatizado")
    
    await ctx.send(embed=embed, view=SupportView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_bateponto(ctx):
    embed = discord.Embed(
        title="",
        description="Você está no **Painel de Bate Ponto** da **UNIMED**.\n\n"
                    "📌 **INSTRUÇÕES:**\n"
                    "• Clique em **INICIAR** ao começar o seu turno.\n"
                    "• Clique em **FECHAR** assim que finalizar o seu turno.\n"
                    "• Não esqueça de fechar o ponto antes de sair da cidade.\n\n"
                    "*A dedicação, o respeito e o compromisso começam aqui.*\n*Bom trabalho!*",
        color=0x2ecc71
    )
    embed.set_author(name="SISTEMA DE BATE PONTO", icon_url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
    embed.set_image(url="https://media.discordapp.net/attachments/1293346011691089992/1526567051412508824/content.png?ex=6a9b631b&is=6a9a119b&hm=bb544feeacd842de5bd189b27962b3575c2b498b40d061b481bd2620d58cc8ea&=&format=webp&quality=lossless&width=2048&height=683")
    embed.set_footer(text="Sistema Automatizado por UNIMED DRP")
    
    await ctx.send(embed=embed, view=BatePontoView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def forcar_rank(ctx):
    await ctx.send("⏳ Gerando ranking...")
    if not MONGO_URI: return
    channel = bot.get_channel(1545433966427766945)
    if not channel: return
    
    guild = channel.guild
    cargo_id = 1545262380286611559
    cargo = guild.get_role(cargo_id)
    
    all_users = await db.bate_ponto_horas.find({}).to_list(length=1000)
    
    rank_list = []
    for u in all_users:
        member = guild.get_member(u["user_id"])
        if member and cargo in member.roles:
            rank_list.append((member, u.get("total_seconds", 0)))
            
    rank_list.sort(key=lambda x: x[1], reverse=True)
    
    desc = ""
    for idx, (mem, secs) in enumerate(rank_list[:20], 1):
        horas, remainder = divmod(secs, 3600)
        minutos, _ = divmod(remainder, 60)
        desc += f"**{idx}º** | {mem.mention} - `{horas:02d}h {minutos:02d}m`\n"
        
    if not desc:
        desc = "Nenhum membro possui horas registradas."
        
    import datetime
    embed = discord.Embed(
        title="🏆 Ranking Mensal de Horas (UNIMED)",
        description=desc,
        color=0xf1c40f
    )
    embed.set_footer(text=f"Fechamento: {datetime.datetime.now().strftime('%m/%Y')}")
    
    await channel.send(embed=embed)
    await ctx.send("✅ Ranking gerado com sucesso!")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_admin(ctx):
    embed = discord.Embed(
        title="",
        description="Você está no **Painel Administrativo** da **UNIMED**.\n\n"
                    "📌 **AÇÕES DISPONÍVEIS:**\n"
                    "• **Advertência:** Aplicar advertências a membros.\n"
                    "• **Exoneração:** Registrar a saída/demissão de um membro.\n"
                    "• **Upamento:** Registrar a promoção de um membro.\n"
                    "• **Rebaixamento:** Registrar o rebaixamento de um membro.\n\n"
                    "*Painel de uso exclusivo da alta cúpula.*",
        color=0x2ecc71
    )
    embed.set_author(name="SISTEMA ADMINISTRATIVO", icon_url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1544042117335359499/1545265874003566692/6AD20457-458D-45F4-AC6D-FF51927FF902.png?ex=6a9b847e&is=6a9a32fe&hm=c64697b4f99600e83981c767442c28b710260447ab675bba4daf748b6c5d45b6")
    embed.set_image(url="https://media.discordapp.net/attachments/1293346011691089992/1526567051412508824/content.png?ex=6a9b631b&is=6a9a119b&hm=bb544feeacd842de5bd189b27962b3575c2b498b40d061b481bd2620d58cc8ea&=&format=webp&quality=lossless&width=2048&height=683")
    embed.set_footer(text="Sistema Automatizado por UNIMED DRP")
    
    await ctx.send(embed=embed, view=PainelAdminView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def id(ctx):
    roles = list(ctx.guild.roles)
    roles.reverse() # Do mais alto para o mais baixo
    
    msg = "**📋 Lista de Cargos e IDs do Servidor:**\n\n"
    msgs = []
    
    for r in roles:
        if r.is_default(): continue
        
        linha = f"• **{r.name}** - `{r.id}`\n"
        if len(msg) + len(linha) > 1900:
            msgs.append(msg)
            msg = ""
        msg += linha
        
    if msg:
        msgs.append(msg)
        
    for m in msgs:
        await ctx.send(m)

if __name__ == '__main__':
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Erro: Token não configurado.")
