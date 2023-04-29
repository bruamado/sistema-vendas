"""
To Do:
A ser feito:
1. Alterar alternadamente a cor de bg das linhas da TreeView
2. Bindar a tecla tab quando pressionada no EntryProdutos para pressinar o botão 'inserir' automaticamente
3. Bindar a tecla tab quando pressionada no ButtonInsert para retornar o cursor para o EntryValor
4. Ao fechar o programa diretamente pelo windows, sem usar o botão 'fechar' da interface, deve chamar a mesma função
que o botão 'fechar' da interface.
5. Adicionar a função de alterar a descrição do nome do produto, para situações onde ele é inserido incorretamente, por
exemplo
6. Ao clicar no EntryValor, deve limpar a seleção do TreeView, se esta existir.
7. Ao clicar no EntryProdutos, deve limpar a seleção do TreeView, se esta existir.
8. Remover a mensagem de status 'Aguardando motivo de cancelamento' ao fechar o popup de cancelamento de venda, sem
ter concluido o cancelamento.
9. Alterar a descrição do botão 'Excluir' para 'Cancelar venda' ao clicar com o botão direito em uma venda dentro da
TreeView
10. Aplicar máscara no display do labelValorTotal para separar a casa do milhar com .
"""

import sys
import time
import tkinter as tk
import sqlite3
import tkinter.messagebox
import traceback
from datetime import datetime
from tkinter import ttk
from string import capwords
import threading

dbName = 'vendas.db'
# Se o banco não existir ele cria e conecta, senão só conecta
db = sqlite3.connect(dbName)
cursor = db.cursor()

# Cria a tabela no banco de dados do arquivo acima se a tabela não existir
cursor.execute('''CREATE TABLE IF NOT EXISTS vendas
               (id INTEGER PRIMARY KEY AUTOINCREMENT, dt DATE DEFAULT (datetime('now', 'localtime')), 
               valor FLOAT, desc TEXT, deleted BOOLEAN DEFAULT('FALSE'), deleted_reason TEXT)''')


# Funcionalidades da aplicação
def inserirVenda():
    try:
        valor = float(entryValor.get().replace(",", "."))
        produtosInput = entryProdutos.get()
        if valor and produtosInput:
            now = datetime.now()
            dt = now.strftime('%Y-%m-%d %H:%M:%S')
            produtosInput = produtosInput.replace("+", ";")
            produtosList = produtosInput.split(';')
            produtos = []
            for i in range(len(produtosList)):  # Retira os espaços antes e depois de cada item e passa para minusculo
                produtosList[i] = produtosList[i].strip().lower()
                if produtosList[i] != '':  # Remove as strings vazias
                    produtos.append(produtosList[i])
            if not produtos:
                print('ERRO: Você precisa inserir pelo menos um produto!\n\n')

            produtosStr = ''
            for i in range(len(produtos)):
                if produtos[i] != '':
                    if i + 1 >= len(produtos):
                        produtosStr = produtosStr + produtos[i]
                    else:
                        produtosStr = produtosStr + produtos[i] + ';'
            try:
                query = f"INSERT INTO vendas (dt, valor, desc) VALUES ('{dt}', {valor}, {repr(produtosStr)})"
                cursor.execute(query)
                db.commit()
            except sqlite3.Error as er:
                print('SQLite error: %s' % (' '.join(er.args)))
                print("Exception class is: ", er.__class__)
                print('SQLite traceback: ')
                exc_type, exc_value, exc_tb = sys.exc_info()
                print(traceback.format_exception(exc_type, exc_value, exc_tb))
                print('Houve um erro ao adicionar a venda. Provavelmente devido a descrição dos produtos.')
                atualizaStatus('ERRO: Não foi possível inserir esta venda. Tente alterar a descrição do(s) produto(s).')
                logRegister(f"Erro ao inserir a venda:\nValor: {valor}\nProdutos: {produtosStr}")
                return
            _dt = now.strftime('%H:%M:%S')
            _id = cursor.lastrowid
            _valor = '{:.2f}'.format(valor).replace('.', ',')
            _produtos = produtosStr.replace(';', ' + ')
            _produtos = capwords(_produtos)
            treeViewInsert(_id, _dt, _valor, _produtos, 'FALSE')
            entryValor.delete(0, tk.END)
            entryProdutos.delete(0, tk.END)
            vendasTreeView.selection_remove(vendasTreeView.focus())
            entryValor.focus_set()
            print('Venda inserida:')
            print(f'ID: {_id} ; dt = {_dt} ; valor = {_valor} ; produtos = {_produtos}')
            atualizaStatus('Venda inserida com sucesso.', 2)
            atualizaValorTotal()
        else:
            print('Nenhum produto foi inserido!')
            atualizaStatus('Para inserir uma venda, é necessário inserir ao menos um produto.')
    except ValueError:
        print('Nenhum valor foi inserido!')
        atualizaStatus('Para insirir uma venda, é necessário inserir o valor e ao menos um produto.')


def popupDeletarVenda():

    def confirmDelete():
        deletedReason = entryDeletedReason.get()
        if len(deletedReason) < 5:
            tkinter.messagebox.showwarning('Aviso', 'É obrigatório inserir uma justificativa '
                                                    'com no mínimo 5 caracteres.')
        else:
            if tkinter.messagebox.askokcancel("Cancelamento", "Você tem certeza de que quer cancelar esta venda?\n"
                                                              "Isso não poderá ser desfeito!"):
                try:
                    query = f"UPDATE vendas SET deleted = 'TRUE', deleted_reason = {repr(deletedReason)} " \
                            f"WHERE id = {itemId}"
                    cursor.execute(query)
                    vendasTreeView.item(itemSelecionado, tags=['deleted', 't1'])
                    vendasTreeView.set(itemSelecionado, 'deleted', 'TRUE')
                    vendasTreeView.selection_remove(itemSelecionado)
                    atualizaStatus('Venda cancelada com sucesso.')
                    tkinter.messagebox.showinfo('Aviso', 'A venda foi cancelada com sucesso.')
                    topMotivoDel.destroy()
                    atualizaValorTotal()
                    entryValor.focus_set()
                except sqlite3.Error as er:
                    print('SQLite error: %s' % (' '.join(er.args)))
                    print("Exception class is: ", er.__class__)
                    print('SQLite traceback: ')
                    exc_type, exc_value, exc_tb = sys.exc_info()
                    print(traceback.format_exception(exc_type, exc_value, exc_tb))
                    print('Houve um erro ao cancelar esta venda. Provavelmente devido ao motivo do cancelamento:')
                    print('Motivo: ', end='')
                    print(deletedReason)
                    atualizaStatus('ERRO: Não foi possível cancelar esta venda.')
                    tkinter.messagebox.showerror('Erro', 'Houve um erro ao cancelar esta venda.\n'
                                                         'Tente alterar o motivo do cancelamento.')
                    logRegister(f"Erro ao cancelar a venda:\nValor: {_valor}\nProdutos: {_desc}"
                                f"\nMotivo: {deletedReason}")
                    return

    def onClosing():
        vendasTreeView.selection_remove(itemSelecionado)
        topMotivoDel.destroy()

    labelStatus.configure(text="Aguardando motivo de cancelamento..")
    itemSelecionado = vendasTreeView.focus()
    itemId = vendasTreeView.item(itemSelecionado)['values'][0]
    _dt = vendasTreeView.item(itemSelecionado)['values'][1]
    _valor = vendasTreeView.item(itemSelecionado)['values'][2]
    _desc = vendasTreeView.item(itemSelecionado)['values'][3]
    _deleted = vendasTreeView.item(itemSelecionado)['values'][4]
    if _deleted == 'TRUE':
        tkinter.messagebox.showerror('Erro', 'Esta venda já está cancelada!')
        return

    itemSelecionadoStr = str(f'\nHORA: {_dt} \n VALOR: R$ {_valor} \n PRODUTO(S): {_desc}')

    topMotivoDel = tk.Toplevel(janela)
    topMotivoDel.withdraw()
    topMotivoDel.title('CANCELAR VENDA - Sistema De Vendas')
    topMotivoDel.iconbitmap(r'img\icon.ico')
    topMotivoDel.update_idletasks()  # Update “requested size” from geometry manager
    x = (topMotivoDel.winfo_screenwidth() - topMotivoDel.winfo_reqwidth()) / 2
    y = (topMotivoDel.winfo_screenheight() - topMotivoDel.winfo_reqheight()) / 2
    topMotivoDel.grab_set()
    topMotivoDel.resizable(False, False)
    topMotivoDel.geometry("+%d+%d" % (x - 200, y - 100))

    _rotuloTitulo = tk.Label(topMotivoDel, text="CANCELAR VENDA", font=('Tahoma', 15, 'bold'))
    _rotuloTitulo.grid(row=0, column=0, sticky='WE')
    _vendaSelecionada = tk.Label(topMotivoDel, text="{}\n\nInsira o motivo do cancelamento:".format(itemSelecionadoStr),
                                 font=('Tahoma', 12))
    _vendaSelecionada.grid(row=1, column=0, sticky='WE')
    entryDeletedReason = tk.Entry(topMotivoDel, width=50, font=("Arial", 14))
    entryDeletedReason.grid(row=2, column=0, padx=10, pady=10, sticky='WE')
    buttonDeletedReason = tk.Button(topMotivoDel, width=10, text='Confirmar', command=confirmDelete)
    buttonDeletedReason.grid(row=3, column=0, pady=(0, 10))

    topMotivoDel.deiconify()
    entryDeletedReason.focus_set()
    topMotivoDel.protocol("WM_DELETE_WINDOW", onClosing)
    topMotivoDel.mainloop()


def consultar():
    pass


def atualizaValorTotal():
    _valorTotal = 0
    for row in vendasTreeView.get_children():
        rowValor = vendasTreeView.item(row)['values'][2].replace(',', '.')
        rowValor = float(rowValor)
        if vendasTreeView.item(row)['values'][4] != 'TRUE':
            _valorTotal += rowValor
    _valorTotal = '{:.2f}'.format(_valorTotal)
    _valorTotal = _valorTotal.replace('.', ',')
    labelValorTotal.configure(text=f'Total: R$ {_valorTotal}')


def timerEnd(timerName):
    if timerName == 's':  # Status Timer
        labelStatus.configure(text='')
    if timerName == 'v':  # Valor Total Timer
        # Esconde o valor total
        buttonExibeValorTotal.configure(image=imgEyeClosed)
        labelValorTotal.configure(image=imgTotalHidden)


def atualizaStatus(msg='', t=5):
    labelStatus.configure(text=msg)
    timerStatus = threading.Timer(t, timerEnd, 's')
    timerStatus.start()


def botaoSairFunc():
    if tkinter.messagebox.askokcancel("Sair", "Você deseja fechar o sistema de vendas?"):
        db.close()
        janela.destroy()


def botaoMinimizarFunc():
    vendasTreeView.selection_clear()
    janela.state(newstate='iconic')


def bClickExibeValorTotal():
    _imgAtual = buttonExibeValorTotal.config()['image'][4]
    if _imgAtual != 'pyimage2':
        # Esconde o valor total
        buttonExibeValorTotal.configure(image=imgEyeClosed)
        labelValorTotal.configure(image=imgTotalHidden)
    else:
        # Exibe o valor total
        buttonExibeValorTotal.configure(image=imgEye)
        labelValorTotal.configure(image='')
        timerStatus = threading.Timer(5, timerEnd, 'v')  # Esconde o valor total depois de 5 segundos
        timerStatus.start()


# Funcões
def logRegister(msg):
    now = datetime.now()
    _dt = now.strftime("%d/%m/%Y - %H:%M:%S")
    logFileName = "logError.txt"
    log = open(logFileName, "at+")
    msgToRegister = _dt + "\n" + msg + "\n\n\n"
    log.writelines(msgToRegister)
    log.close()
    print("Log registrado.")
    return


def validarNumero(entrada):
    if entrada == "":
        return True
    try:
        valor = float(entrada.replace(",", "."))
        if str(valor)[::-1].find('.') > 2:
            return False
        return True
    except ValueError:
        return False


def getMes(m):
    print(int(m))
    match int(m):
        case 1: return 'Janeiro'
        case 2: return 'Fevereiro'
        case 3: return 'Março'
        case 4: return 'Abril'
        case 5: return 'Maio'
        case 6: return 'Junho'
        case 7: return 'Julho'
        case 8: return 'Agosto'
        case 9: return 'Setembro'
        case 10: return 'Outubro'
        case 11: return 'Novembro'
        case 12: return 'Dezembro'
        case _: return None


def inicializaLista():
    # Atualiza a labelData
    now = datetime.now()
    mes = getMes(now.strftime('%m'))
    labelData.configure(text=now.strftime(f'%d de {mes} de %Y'))
    atualizaStatus('Conectando com o banco de dados..', 2)
    try:
        query = "SELECT * FROM vendas WHERE STRFTIME('%Y-%m-%d', dt) = DATE('now', 'localtime')"
        cursor.execute(query)
        getVendasHoje = cursor.fetchall()
        for linha in getVendasHoje:
            dtTime = time.strptime(linha[1], '%Y-%m-%d %H:%M:%S')
            _id = linha[0]
            _dt = time.strftime('%H:%M:%S', dtTime)
            _valor = '{:.2f}'.format(linha[2]).replace('.', ',')
            _produtos = linha[3].replace(';', ' + ')
            _produtos = capwords(_produtos)
            _deleted = linha[4]
            if linha[4] == 'TRUE':
                vendasTreeView.insert('', 0, values=(_id, _dt, _valor, _produtos, _deleted), tags=['t1', 'deleted'])
            else:
                vendasTreeView.insert('', 0, values=(_id, _dt, _valor, _produtos, _deleted), tags=['t1'])
        atualizaValorTotal()
        entryValor.focus_set()
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
        print('Houve um erro recuperar as vendas do dia do banco de dados.')
        atualizaStatus('ERRO: Não foi possível recuperar as vendas do banco de dados.', 20)
        logRegister("ERRO: Não foi possível recuperar as vendas do banco de dados ao inicializar o app.")
        return


def treeViewInsert(idT, dtT, valorT, descT, deletedT):
    """
    Adiciona uma linha no treeView com os parâmetros passados
    """
    vendasTreeView.insert('', 0, values=(idT, dtT, valorT, descT, deletedT), tags=['t1'])


def mostrarMenu(event):
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


# Inicializa a janela principal
janela = tk.Tk()
janela.title('SISTEMA DE VENDAS - Vender')
janela.iconbitmap(r'img\icon.ico')
janela.attributes('-fullscreen', True)
janela.resizable(False, False)

# Inicializando os Widgets e posicionando
janela.grid_columnconfigure(1, weight=1)
janela.grid_rowconfigure(6, weight=1)

# linha 0
labelTitulo = tk.Label(janela, text="SISTEMA DE VENDAS", font=('Tahoma', 20, 'bold'))
labelTitulo.grid(row=0, column=0, columnspan=2, sticky='WE')
imgLogo = tk.PhotoImage(file=r'img\logo.png')
labelImgLogo = tk.Label(janela, image=imgLogo)
labelImgLogo.grid(row=0, rowspan=2, column=0, padx=(10, 0), pady=(10, 0), sticky='W')
buttonMinimizar = tk.Button(janela, text="Minimizar", command=botaoMinimizarFunc)
buttonMinimizar.grid(row=0, column=1, padx=(0, 30), sticky="NE")
buttonSair = tk.Button(janela, text="Sair", command=botaoSairFunc)
buttonSair.grid(row=0, column=1, sticky="NE")

# linha 1
labelSubTitulo = tk.Label(janela, text="Inserir venda", font=('Tahoma', 15, 'italic'))
labelSubTitulo.grid(row=1, column=0, columnspan=2, sticky='WE')

# linha 2
labelValor = tk.Label(janela, text="Valor:", font=('Sans Serif', 14, 'bold'))
labelValor.grid(row=2, column=0, padx=(10, 0), sticky='W')
labelProdutos = tk.Label(janela, text="Produto(s):", font=('Sans Serif', 14, 'bold'))
labelProdutos.grid(row=2, column=0, columnspan=2, sticky='W', padx=(125, 0))
labelImgLogo.lift()

# linha 3
entryValor = tk.Entry(janela, width=7, font=("Arial", 14))
entryValor.grid(row=3, column=0, padx=(10, 0), sticky='W')
entryProdutos = tk.Entry(janela, width=30, font=("Arial", 14))
entryProdutos.grid(row=3, column=0, padx=(100, 10), sticky='W')
buttonInserir = tk.Button(janela, text="Inserir", width=10, font=('Sans Serif Bold', 12, 'bold'), command=inserirVenda)
buttonInserir.grid(row=3, column=1, sticky="W")

# linha 4
labelData = tk.Label(janela, text="", font=("Calibri", 15))
labelData.grid(row=4, column=0, columnspan=2, sticky='WE')

# linha 5
imgEyeClosed = tk.PhotoImage(file=r'img\eye_closed.png')
imgEye = tk.PhotoImage(file=r'img\eye.png')
buttonExibeValorTotal = tk.Button(janela, image=imgEyeClosed, width=35, height=35, borderwidth=0,
                                  command=bClickExibeValorTotal)
buttonExibeValorTotal.grid(row=5, column=0, padx=(10, 0), pady=(10, 0), sticky='W')
imgTotalHidden = tk.PhotoImage(file=r'img\total_hidden.png')
labelValorTotal = tk.Label(janela, text="Total: R$ 0,00", image=imgTotalHidden, font=("Arial", 20, 'bold'))
labelValorTotal.grid(row=5, column=0, padx=(50, 0), pady=(5, 0), sticky='W')

# linha 6
vendasTreeView = ttk.Treeview(janela, columns=("id", "dt", "valor", "desc", "deleted"), show='headings',
                              height=10, displaycolumns=('dt', 'valor', 'desc'))
vendasTreeView.heading('id', text='ID')
vendasTreeView.heading('dt', text='Hora')
vendasTreeView.heading('valor', text='Valor', )
vendasTreeView.heading('desc', text='Produto(s)', anchor='w')
vendasTreeView.heading('deleted', text='deleted')
vendasTreeView.column('dt', anchor='center', minwidth=0, width=120, stretch=False)
vendasTreeView.column('valor', anchor='w', minwidth=0, width=150, stretch=False)
vendasTreeView.column('desc', anchor='w')
vendasTreeView.grid(row=6, column=0, columnspan=2, padx=(10, 30), pady=(10, 0), sticky="NSEW")
scrollbar = tk.Scrollbar(janela, orient="vertical")
scrollbar.config(command=vendasTreeView.yview)
scrollbar.grid(row=6, column=1, pady=(10, 0), padx=(0, 10), sticky="NSE")

# linha 7
labelStatus = tk.Label(janela, text="Inicializando..", font=("Sans Serif", 10, 'bold'))
labelStatus.grid(row=7, column=0, columnspan=2, sticky="W", padx=(10, 0))
developedBy = tk.Label(janela, text="Desenvolvido por Bruno Amado.", font=("Arial", 10, 'italic'))
developedBy.grid(row=7, column=1, sticky="SE")

# Sem linha definida
menu = tk.Menu(janela, tearoff=0)
menu.add_command(label="Excluir", command=popupDeletarVenda)

# Style
style = ttk.Style()
style.configure("Treeview.Heading", font=('Helvetica', 20, 'bold'))
style.configure("Treeview.Heading", font=('Helvetica', 20, 'bold'))
style.configure('Treeview', rowheight=30)
style.map('Treeview', background=[('selected', '#abdbff')])

# Inicializa tags para estilização
vendasTreeView.tag_configure('t1', font=("Open Sans", 15))
vendasTreeView.tag_configure('deleted', background='#ffd1d1')

# Configurando as restrições dos widgets de entrada
entryValor.config(validate="key", validatecommand=(janela.register(validarNumero), "%P"))
entryProdutos.config(validate="none")

# Bindando ações aos widgets
entryValor.bind("<Return>", lambda event: entryProdutos.focus_set())
entryProdutos.bind("<Return>", lambda event: buttonInserir.invoke())
buttonInserir.bind("<Return>", lambda event: buttonInserir.invoke())
vendasTreeView.bind("<Button-3>", mostrarMenu)

inicializaLista()
janela.mainloop()
