import streamlit as st
import time # Importado apenas para simular o "Verificar Status"

# ==========================================
# 🛑 CONTROLE DE MANUTENÇÃO (LIGAR/DESLIGAR)
# ==========================================
EM_MANUTENCAO = False  # Mude para False quando quiser liberar o site normal

if EM_MANUTENCAO:
    # --- CONFIGURAÇÃO DA TELA DE MANUTENÇÃO ---
    st.set_page_config(page_title="Em Manutenção", page_icon="🚧", layout="centered")

    # Layout: Coluna da esquerda (Mensagem) e direita (Status)
    col1, col2 = st.columns([2, 1])

    with col1:
        st.title("🚧 Estamos em Manutenção")
        st.markdown("""
        ### O sistema está evoluindo.
        Estamos implementando uma atualização radical para a **Versão 2.0**.
        
        **O que muda?**
        * 🚀 Melhor performance.
        * 📂 Geração de documentos mais rápida.
        * ✨ Nova interface visual.
        
        Agradecemos a paciência!
        """)
        st.write("")
        st.info("Status atual: **Finalizando ajustes no servidor**")
        
        # Barra de progresso visual
        st.progress(85)

    with col2:
        st.subheader("🛠️ Ferramentas")
        st.write("Precisa de ajuda urgente?")
        
        # Botão simples de status (sem banco de dados)
        if st.button("🔄 Verificar Status"):
            with st.spinner("Checando servidores..."):
                time.sleep(1.5) # Simula um carregamento
                st.success("Sistemas: 🟢 Online")
                st.warning("App: 🟡 Em Atualização")
        
        st.divider()
        
        st.caption("Dúvidas ou suporte:")
        st.code("carlos.car.cati@gmail.com", language="text")

    st.divider()
    st.caption("© 2026 Equipe de Desenvolvimento - PRODESP")
    
    # 🛑 BLOQUEIO TOTAL
    # O comando abaixo impede que o resto do código rode.
    st.stop() 

# ==========================================
# 🚀 SEU CÓDIGO DO SITE NORMAL COMEÇA AQUI
# ==========================================
# Tudo abaixo desta linha só vai aparecer quando você mudar
# EM_MANUTENCAO = False lá no topo.

st.title("Sistema de Relatórios v2.0")
st.write("Bem-vindo ao sistema atualizado!")

# ... Cole aqui suas 1000 linhas de código do sistema principal ...
import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
import io
import json
import os
import tempfile
import base64
from datetime import date
from PIL import Image
import uuid

# --- 1. CONFIGURAÇÃO INICIAL E CSS ---
st.set_page_config(page_title="Parecer Técnico v16 (Item Personalizado)", layout="wide")

st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] > div > button {
        border-color: #ff4b4b;
        color: #ff4b4b;
    }
    div[data-testid="stVerticalBlock"] > div > button:hover {
        background-color: #ff4b4b;
        color: white;
    }
    .stButton > button[kind="primary"] {
        background-color: #4CAF50;
        color: white;
        border: none;
    }
    .img-container {
        border: 1px solid #ddd;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        text-align: center;
        background-color: #f9f9f9;
    }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- 2. LISTA MESTRA DE OPÇÕES ---
OPCOES_LISTA = [
    "Inconsistências em Ficha do imóvel",
    "Inconsistências em Sobreposição com outros IRs",
    "Inconsistência em Sobreposição com Unidade de Conservação de Uso Sustentável",
    "Outras Sobreposições",
    "Inconsistências em Áreas embargadas",
    "Inconsistências em Assentamentos",
    "Inconsistências em UC",
    "Inconsistências em Cobertura do solo", 
    "Inconsistências em Infraestrutura e utilidade pública",
    "Inconsistências em Reservatório para abastecimento ou geração de energia",
    "Inconsistências em APP hidrografia",
    "Inconsistências em APP Relevo",
    "Inconsistências em Uso restrito",
    "Inconsistências em outras APPs",
    "Inconsistências em RL averbada, RL aprovada e não averbada",
    "Inconsistências em Área de RL exigida por lei",
    "Inconsistências em Localização e cobertura do solo",
    "Inconsistências em Regularidade do IR",
    "Inconsistência Adicional",
    "Observação",
    "Item Personalizado ✏️"  # <--- NOVA OPÇÃO
]

# --- 3. GERENCIAMENTO DE ESTADO ---
if 'dados' not in st.session_state:
    st.session_state['dados'] = {
        "car": "", "sp_not": "", "imovel": "", 
        "nome": "", "doc": "", "cidade": "Mogi das Cruzes",
        "itens": [], 
        "textos": {}, 
        "imagens_b64": {} 
    }

if 'uploader_ids' not in st.session_state:
    st.session_state['uploader_ids'] = {}

# --- 4. FUNÇÕES DE CALLBACK ---

def adicionar_item():
    opcao = st.session_state.get("selecao_adicionar")
    if opcao:
        novo_id = str(uuid.uuid4()) 
        
        # Verifica se é o item personalizado
        eh_personalizado = (opcao == "Item Personalizado ✏️")
        
        # Se for personalizado, o título começa vazio (ou com um placeholder), senão pega o da lista
        titulo_inicial = "" if eh_personalizado else opcao
        
        novo_item = {
            "id": novo_id, 
            "titulo": titulo_inicial, 
            "custom": eh_personalizado # Marca flag para sabermos que este é editável
        }
        st.session_state['dados']['itens'].append(novo_item)

def remover_item(id_item):
    st.session_state['dados']['itens'] = [
        item for item in st.session_state['dados']['itens'] if item['id'] != id_item
    ]
    if id_item in st.session_state['dados']['textos']:
        del st.session_state['dados']['textos'][id_item]
    if id_item in st.session_state['dados']['imagens_b64']:
        del st.session_state['dados']['imagens_b64'][id_item]

def processar_upload(id_item):
    uid = st.session_state['uploader_ids'].get(id_item, 0)
    key_widget = f"uploader_{id_item}_{uid}"
    uploaded_file = st.session_state.get(key_widget)
    if uploaded_file:
        try:
            uploaded_file.seek(0)
            bytes_data = uploaded_file.read()
            b64_str = base64.b64encode(bytes_data).decode('utf-8')
            if id_item not in st.session_state['dados']['imagens_b64']:
                st.session_state['dados']['imagens_b64'][id_item] = []
            st.session_state['dados']['imagens_b64'][id_item].append(b64_str)
            st.session_state['uploader_ids'][id_item] = uid + 1
        except Exception as e:
            st.error(f"Erro no processamento: {e}")

# --- 5. OUTRAS FUNÇÕES ---

def obter_data_extenso():
    meses = {1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril', 5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto', 9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'}
    hj = date.today()
    return f"{hj.day} de {meses[hj.month]} de {hj.year}"

def limpar_tudo():
    st.session_state['dados'] = {
        "car": "", "sp_not": "", "imovel": "", 
        "nome": "", "doc": "", "cidade": "", 
        "itens": [], "textos": {}, "imagens_b64": {}
    }
    st.session_state['uploader_ids'] = {}
    campos = ["car", "sp_not", "imovel", "nome", "doc", "cidade"]
    for c in campos:
        st.session_state[f"input_{c}"] = ""

def limpar_campo_cabecalho(key_sulfix):
    st.session_state[f"input_{key_sulfix}"] = ""

def remover_imagem_especifica(id_item, index):
    if id_item in st.session_state['dados']['imagens_b64']:
        lista = st.session_state['dados']['imagens_b64'][id_item]
        if 0 <= index < len(lista):
            lista.pop(index)
            if not lista:
                del st.session_state['dados']['imagens_b64'][id_item]

def formatar_documento(n):
    if not n: return ""
    n = "".join(filter(str.isdigit, str(n)))
    if len(n) == 11: return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"
    elif len(n) == 14: return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
    return n

def b64_para_tempfile(b64_str):
    try:
        bytes_data = base64.b64decode(b64_str)
        file_obj = io.BytesIO(bytes_data)
        img = Image.open(file_obj)
        if img.mode in ('RGBA', 'LA'):
            background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
            background.paste(img, img.split()[-1])
            img = background
        img = img.convert('RGB')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
            img.save(tf, format='JPEG', quality=95)
            return tf.name
    except Exception:
        return None

# --- 6. GERAÇÃO DE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', '', 10)
        self.set_xy(-20, 20) 
        self.cell(0, 0, str(self.page_no()), 0, 0, 'R')
        self.ln(20)

    def write_markdown(self, text, line_height=7):
        text = str(text) if text else ""
        text = text.encode('latin-1', 'replace').decode('latin-1')
        linhas = text.split('\n')
        for linha in linhas:
            if not linha.strip():
                self.ln(line_height)
                continue
            self.write(line_height, "      ") 
            partes = linha.split('**')
            for i, parte in enumerate(partes):
                if i % 2 == 1:
                    self.set_font("Arial", 'B', 12)
                else:
                    self.set_font("Arial", '', 12)
                self.write(line_height, parte)
            self.ln(line_height)

def gerar_pdf_bytes():
    try:
        pdf = PDF()
        pdf.set_margins(30, 30, 20)
        pdf.add_page()
        def safe_text(text): return text.encode('latin-1', 'replace').decode('latin-1') if text else ""

        pdf.set_font("Arial", 'B', 14); pdf.cell(0, 8, safe_text("Justificativa do Parecer Técnico"), ln=True, align='C')
        pdf.set_font("Arial", 'B', 12); pdf.cell(0, 6, safe_text(f"CAR: {st.session_state['dados']['car']}"), ln=True, align='C')
        pdf.cell(0, 6, safe_text(f"SP-NOT: {st.session_state['dados']['sp_not']}"), ln=True, align='C'); pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12); pdf.write(6, safe_text("Nome do Imóvel Rural: ")); pdf.set_font("Arial", '', 12); pdf.write(6, safe_text(st.session_state['dados']['imovel'])); pdf.ln(6)
        pdf.set_font("Arial", 'B', 12); pdf.write(6, safe_text("Nome: ")); pdf.set_font("Arial", '', 12); pdf.write(6, safe_text(st.session_state['dados']['nome'])); pdf.ln(6)
        pdf.set_font("Arial", 'B', 12); pdf.write(6, safe_text("CPF/CNPJ: ")); pdf.set_font("Arial", '', 12); pdf.write(6, safe_text(formatar_documento(st.session_state['dados']['doc']))); pdf.ln(10)
        
        for i, item_obj in enumerate(st.session_state['dados']['itens']):
            # Garante que usamos o título atualizado (caso tenha sido editado)
            titulo = item_obj['titulo']
            if not titulo: titulo = "Sem Título Definido"

            id_item = item_obj['id']
            
            pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, safe_text(f"{i+1}. {titulo}"), ln=True)
            
            texto_raw = st.session_state['dados']['textos'].get(id_item, "")
            widget_val = st.session_state.get(f"txt_area_{id_item}")
            if widget_val is not None: texto_raw = widget_val
            
            pdf.write_markdown(texto_raw)
            
            lista_imgs = st.session_state['dados']['imagens_b64'].get(id_item, [])
            if lista_imgs:
                pdf.ln(2)
                for b64_img in lista_imgs:
                    temp_path = b64_para_tempfile(b64_img)
                    if temp_path:
                        try:
                            x_pos = (210 - 120) / 2 
                            if pdf.get_y() > 220: pdf.add_page()
                            pdf.image(temp_path, x=x_pos, w=120)
                            pdf.ln(5)
                        finally:
                            if os.path.exists(temp_path): os.unlink(temp_path)
                pdf.ln(2)
            pdf.ln(4)
            
        pdf.ln(10); pdf.cell(0, 6, "________________________________________", ln=True, align='R')
        pdf.cell(0, 6, safe_text(st.session_state['dados']['nome']), ln=True, align='R')
        cidade_doc = st.session_state['dados']['cidade'] if st.session_state['dados']['cidade'] else "Mogi das Cruzes"
        pdf.cell(0, 6, safe_text(f"{cidade_doc}, {obter_data_extenso()}."), ln=True, align='R')
        return pdf.output(dest='S').encode('latin-1', 'replace')
    except Exception as e: return None

# --- 7. BARRA LATERAL ---
with st.sidebar:
    st.header("🗂️ Arquivos")
    arquivo_upload = st.file_uploader("📂 Carregar Trabalho (.json)", type=["json"])
    
    if arquivo_upload is not None:
        if st.button("🔄 Confirmar Carregamento"):
            try:
                dados_carregados = json.load(arquivo_upload)
                # Compatibilidade legada
                if "selecionados" in dados_carregados and "itens" not in dados_carregados:
                    novos_itens = []
                    novos_textos = {}
                    novas_imgs = {}
                    for nome_antigo in dados_carregados.get("selecionados", []):
                        novo_id = str(uuid.uuid4())
                        novos_itens.append({"id": novo_id, "titulo": nome_antigo, "custom": False})
                        if nome_antigo in dados_carregados.get("textos", {}):
                            novos_textos[novo_id] = dados_carregados["textos"][nome_antigo]
                        img_val = dados_carregados.get("imagens_b64", {}).get(nome_antigo, [])
                        if isinstance(img_val, str): img_val = [img_val]
                        if img_val: novas_imgs[novo_id] = img_val
                    
                    dados_carregados["itens"] = novos_itens
                    dados_carregados["textos"] = novos_textos
                    dados_carregados["imagens_b64"] = novas_imgs

                st.session_state['dados'] = dados_carregados
                for k in ["car", "sp_not", "imovel", "nome", "doc", "cidade"]:
                    st.session_state[f"input_{k}"] = dados_carregados.get(k, "")
                
                st.session_state['uploader_ids'] = {} 
                st.success("✅ Carregado com Sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
    
    st.markdown("---")
    dados_download = json.dumps(st.session_state['dados'], indent=4)
    st.download_button("💾 Salvar Backup", dados_download, "backup_multi_v14.json", "application/json")
    st.markdown("---")
    st.button("🗑️ Limpar Tudo", on_click=limpar_tudo, type="primary")

# --- 8. INTERFACE PRINCIPAL ---
st.title("📄 Gerador de Parecer Técnico (Com Item Personalizável)")

tab_edit, tab_preview = st.tabs(["✍️ Edição", "👁️ Pré-visualização Real (PDF)"])

with tab_edit:
    st.subheader("1. Cabeçalho")
    def campo_com_lixeira(label, key_suffix):
        c_input, c_btn = st.columns([0.85, 0.15])
        with c_input:
            val = st.text_input(label, key=f"input_{key_suffix}")
            st.session_state['dados'][key_suffix] = val
        with c_btn:
            st.write(""); st.write("")
            st.button("🗑️", key=f"del_header_{key_suffix}", on_click=limpar_campo_cabecalho, args=(key_suffix,))

    c1, c2 = st.columns(2)
    with c1:
        campo_com_lixeira("CAR:", "car")
        campo_com_lixeira("SP-NOT (Número):", "sp_not")
        campo_com_lixeira("Nome do Imóvel:", "imovel")
    with c2:
        campo_com_lixeira("Nome do Requerente:", "nome")
        campo_com_lixeira("CPF/CNPJ:", "doc")
        campo_com_lixeira("Cidade:", "cidade")

    st.markdown("---")
    st.subheader("2. Adicionar Inconsistências")
    
    col_sel, col_add = st.columns([0.8, 0.2])
    with col_sel:
        st.selectbox("Escolha o tipo de item para adicionar:", OPCOES_LISTA, key="selecao_adicionar")
    with col_add:
        st.write(""); st.write("") 
        st.button("➕ Adicionar", on_click=adicionar_item, type="primary")

    st.markdown("---")
    
    lista_itens = st.session_state['dados']['itens']
    
    if not lista_itens:
        st.info("Nenhum item adicionado ainda. Use a caixa acima para começar.")
    else:
        st.markdown("""
        > 💡 **Dica de Formatação:** Use dois asteriscos para deixar em negrito.  
        > Exemplo: Digite `**A)** Problema identificado` para sair como **A) Problema identificado**.
        """)
        st.write(f"**Itens no Relatório:** {len(lista_itens)}")
        
        for i, item_obj in enumerate(lista_itens):
            titulo = item_obj['titulo']
            id_item = item_obj['id']
            # Flag para saber se é item customizado
            eh_custom = item_obj.get('custom', False)
            
            numero = i + 1
            
            c_titulo, c_remove = st.columns([0.9, 0.1])
            with c_remove:
                st.write("")
                st.button("🗑️", key=f"btn_del_{id_item}", on_click=remover_item, args=(id_item,), help="Excluir este item")
            
            with c_titulo:
                # Se for custom, o título na barra do expander mostra o que foi digitado ou um aviso
                display_title = titulo if titulo else "(Digite o título do item abaixo...)"
                
                with st.expander(f"**{numero}. {display_title}**", expanded=True):
                    
                    # === CAMPO PARA DIGITAR NOME (SÓ APARECE SE FOR PERSONALIZADO) ===
                    if eh_custom:
                        st.markdown("#### ✏️ Nome do Item Personalizado")
                        novo_titulo = st.text_input("Digite o título deste item:", value=titulo, key=f"titulo_custom_{id_item}")
                        # Atualiza o título no dicionário mestre em tempo real
                        if novo_titulo != titulo:
                            item_obj['titulo'] = novo_titulo
                    # ================================================================

                    chave_txt = f"txt_area_{id_item}"
                    val_inicial = st.session_state['dados']['textos'].get(id_item, "")
                    
                    texto = st.text_area("Descrição:", value=val_inicial, key=chave_txt, height=150, placeholder="Ex: **A)** Inconsistência na área X...")
                    
                    if texto: st.session_state['dados']['textos'][id_item] = texto
                    elif id_item in st.session_state['dados']['textos'] and not texto:
                         del st.session_state['dados']['textos'][id_item]
                    
                    st.markdown("#### 🖼️ Imagens")
                    lista_imgs = st.session_state['dados']['imagens_b64'].get(id_item, [])
                    if lista_imgs:
                        cols_imgs = st.columns(3)
                        for idx_img, img_b64 in enumerate(lista_imgs):
                            with cols_imgs[idx_img % 3]:
                                st.markdown("<div class='img-container'>", unsafe_allow_html=True)
                                st.image(base64.b64decode(img_b64), use_container_width=True)
                                if st.button("❌", key=f"del_img_{id_item}_{idx_img}"):
                                    remover_imagem_especifica(id_item, idx_img)
                                    st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)
                    
                    uid = st.session_state['uploader_ids'].get(id_item, 0)
                    key_uploader = f"uploader_{id_item}_{uid}"
                    st.file_uploader(f"Adicionar imagem", type=['png','jpg','jpeg'], key=key_uploader, on_change=processar_upload, args=(id_item,), label_visibility="collapsed")

with tab_preview:
    st.info("Visualização do PDF.")
    pdf_bytes_preview = gerar_pdf_bytes()
    if pdf_bytes_preview:
        base64_pdf = base64.b64encode(pdf_bytes_preview).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.warning("Preencha os dados.")

# --- DOWNLOADS ---
st.markdown("---")
st.subheader("🚀 Baixar Arquivos")
col_d1, col_d2 = st.columns(2)
nome_safe = st.session_state['dados']['nome'].strip() or "Parecer"
nome_arquivo = "".join([c for c in nome_safe if c.isalnum() or c in (' ','-','_')]).strip()

if st.session_state['dados']['car']:
    # WORD - GERAÇÃO CORRIGIDA
    doc = Document()
    sec = doc.sections[0]; sec.top_margin = Cm(3); sec.bottom_margin = Cm(2); sec.left_margin = Cm(3); sec.right_margin = Cm(2)
    style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(12)
    
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Justificativa do Parecer Técnico"); r.bold=True; r.font.size=Pt(14)
    p = doc.add_paragraph(f"CAR: {st.session_state['dados']['car']}"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.runs[0].bold=True
    p = doc.add_paragraph(f"SP-NOT: {st.session_state['dados']['sp_not']}"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.runs[0].bold=True
    doc.add_paragraph()
    
    p = doc.add_paragraph(); p.add_run("Nome do Imóvel Rural: ").bold=True; p.add_run(st.session_state['dados']['imovel'])
    p = doc.add_paragraph(); p.add_run("Nome: ").bold=True; p.add_run(st.session_state['dados']['nome'])
    p = doc.add_paragraph(); p.add_run("CPF/CNPJ: ").bold=True; p.add_run(formatar_documento(st.session_state['dados']['doc']))
    doc.add_paragraph()
    
    for i, item_obj in enumerate(st.session_state['dados']['itens']):
        # Garante título para o word
        titulo = item_obj['titulo']
        if not titulo: titulo = "Item Sem Título"
        id_item = item_obj['id']
        
        p = doc.add_paragraph(f"{i+1}. {titulo}"); p.runs[0].bold=True
        
        texto_item = st.session_state['dados']['textos'].get(id_item, "")
        widget_val = st.session_state.get(f"txt_area_{id_item}")
        if widget_val is not None: texto_item = widget_val
        
        # --- PARSER MARKDOWN PARA WORD ---
        linhas = texto_item.split('\n')
        
        for linha in linhas:
            if not linha:
                doc.add_paragraph()
                continue
            
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Cm(1.25)
            
            partes = linha.split('**')
            for idx, parte in enumerate(partes):
                run = p.add_run(parte)
                if idx % 2 == 1: 
                    run.bold = True

        lista_imgs = st.session_state['dados']['imagens_b64'].get(id_item, [])
        for b64_img in lista_imgs:
            temp_path = b64_para_tempfile(b64_img)
            if temp_path:
                try:
                    doc.add_paragraph()
                    doc.add_picture(temp_path, width=Cm(14))
                    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    doc.add_paragraph()
                except Exception: pass
                finally:
                    if os.path.exists(temp_path): os.unlink(temp_path)

    doc.add_paragraph("\n\n")
    p = doc.add_paragraph("________________________________________"); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p = doc.add_paragraph(st.session_state['dados']['nome']); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    cidade_doc = st.session_state['dados']['cidade'] if st.session_state['dados']['cidade'] else "Mogi das Cruzes"
    p = doc.add_paragraph(f"{cidade_doc}, {obter_data_extenso()}."); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    buffer_word = io.BytesIO(); doc.save(buffer_word); buffer_word.seek(0)
    with col_d1:
        st.download_button("⬇️ Baixar Word (.docx)", buffer_word, f"{nome_arquivo}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

if pdf_bytes_preview:
    with col_d2:
        st.download_button("⬇️ Baixar PDF (.pdf)", pdf_bytes_preview, f"{nome_arquivo}.pdf", "application/pdf")