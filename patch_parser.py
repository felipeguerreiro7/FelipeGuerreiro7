import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\Felip\OneDrive\Área de Trabalho\Projeto pessoal\Sugestao_Alocacao\alocacaoautomatica.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

before = lines[:215]
after  = lines[235:]

new_parser = """\
if arquivo:
    df_raw = pd.read_excel(arquivo, header=None)
    idx_ativo, idx_pos, idx_qtd, idx_pm = 0, 11, 7, 8

    def find_col(cols, *terms):
        for term in terms:
            for i, c in enumerate(cols):
                if c.strip() == term:
                    return i
        return None

    for i, row in df_raw.iterrows():
        txt = " ".join([str(x).upper() for x in row])

        for cell in row:
            s = str(cell)
            if "Conta:" in s or "CONTA:" in s:
                conta_id = s.split("|")[0].replace("Conta:", "").replace("CONTA:", "").strip()
                break

        if "SALDO DISPONIVEL" in txt or "SALDO DISPONÍVEL" in txt:
            try:
                next_row = df_raw.iloc[i + 1]
                for col_idx in [2, 1, 0]:
                    v = formatar_valor(next_row.iloc[col_idx])
                    if v > 0:
                        saldo_corretora = v
                        break
            except Exception:
                pass

        if "ATIVO" in txt and "POSI" in txt:
            cols = [str(x).upper().strip() for x in row]
            ia = find_col(cols, "ATIVO")
            ip = find_col(cols, "POSIÇÃO", "POSICAO", "POSI\\u00c7\\u00c3O")
            if ia is not None and ip is not None:
                idx_ativo, idx_pos = ia, ip
                iq = find_col(cols, "QTDE.", "QTD. TOTAL", "QTDE")
                if iq is not None: idx_qtd = iq
                ipm = find_col(cols, "PREÇO MÉDIO", "PRECO MEDIO")
                if ipm is not None: idx_pm = ipm
            continue

        nome_p = str(row.iloc[idx_ativo]).strip()
        if nome_p not in ("nan", "") and "TOTAL" not in nome_p.upper():
            try:
                v_pos = formatar_valor(row.iloc[idx_pos])
            except Exception:
                v_pos = 0.0
            if v_pos > 1.0:
                cat = classificar_ativo_mestre(nome_p)
                if cat in carteira_lida:
                    carteira_lida[cat] += v_pos
                ativos_detalhados.append({
                    "Ativo": nome_p, "Ticker": limpar_ticker(nome_p),
                    "Qtd": formatar_valor(row.iloc[idx_qtd]) if idx_qtd < len(row) else 0.0,
                    "PM":  formatar_valor(row.iloc[idx_pm])  if idx_pm  < len(row) else 0.0,
                    "Total": v_pos, "Cat": cat
                })

"""

result = before + [new_parser] + after
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(result)

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
try:
    compile(content, 'alocacaoautomatica.py', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'SyntaxError at line {e.lineno}: {e.msg}')
    print(f'  -> {e.text}')
