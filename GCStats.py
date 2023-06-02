import requests
from datetime import date, datetime
import calendar
import pandas as pd
import tkinter as tk
from tkinter import font as tkfont
from tkinter import IntVar

cookies = {
    'gclubsess': ''
}

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
}

today = date.today()
current_year = today.year
current_month = today.month

url_template = 'https://gamersclub.com.br/players/get_playerLobbyResults/{}-{:02}/{}'

# Function to fetch results and update the progress label
def fetch_results():
    # Hide existing widgets
    gclubsess_label.grid_forget()
    entry_frame.grid_forget()
    fetch_button.grid_forget()
    start_year_label.grid_forget()
    start_year_entry.grid_forget()
    run_loop_checkbox.grid_forget()

    # Create and place the loading label
    loading_label = tk.Label(root, text="Carregando...", bg="#222222", fg="white", font=default_font)
    loading_label.grid(row=3, column=0, pady=10)
    root.update()

    gclubsess = entry.get()
    cookies['gclubsess'] = gclubsess

    start_year = int(start_year_entry.get())


    start_date = date(start_year, 1, 1)
    today = date.today()
    current_year = today.year
    current_month = today.month


    data_list = []
    for year in range(start_date.year, current_year + 1):
        start_month = 1 if year == start_date.year else 1
        end_month = current_month if year == current_year else 12

        for month in range(start_month, end_month + 1):
            month_end = calendar.monthrange(year, month)[1]
            url = url_template.format(year, month, 1)
            r = requests.get(url, cookies=cookies, headers=headers)
            json_data = r.json()
            total_pages = int(json_data['pagination']['pages_total'])
            progress_label.config(text=f"Processing data for {year}-{month:02}, total pages: {total_pages}", pady=10)
            root.update()

            for page in range(1, total_pages + 1):
                url = url_template.format(year, month, page)
                r = requests.get(url, cookies=cookies, headers=headers)
                json_data = r.json()

                for item in json_data['lista']:
                    room_a_vitoria = item['room_a_vitoria']
                    room_a_player = item['room_a_player']
                    score_ally = item['score_a'] if room_a_player else item['score_b']
                    score_enemy = item['score_b'] if room_a_player else item['score_a']
                    if (room_a_player and room_a_vitoria) or (not room_a_player and not room_a_vitoria):
                        vitória = 1
                    else:
                        vitória = 0

                    data_dict = {
                        'Partida': item['idlobby_game'],
                        'Mapa': item['map_name'],
                        'Kills': item['nb_kill'],
                        'Assists': item['assist'],
                        'Mortes': item['death'],
                        'Data': datetime.strptime(item['created_at'], "%d/%m/%Y %H:%M"),
                        'PontosVar': item['diference'],
                        'Pontos': item['rating_final'],
                        'Score': f"{score_ally}:{score_enemy}",
                        'id': json_data['currentUser']['id'],
                        'Vitória' : vitória
                    }
                    
                    partida_url = f"https://gamersclub.com.br/lobby/match/{data_dict['Partida']}/1"
                    r = requests.get(partida_url, cookies=cookies, headers=headers)
                    partida_json = r.json()
                    

                    run_loop = run_loop_var.get()
                    if run_loop:
                        for team in [partida_json['jogos']['players']['team_a'], partida_json['jogos']['players']['team_b']]:
                            for player_data in team:
                                if player_data['idplayer'] == data_dict['id']:
                                    data_dict['firstkill'] = player_data['firstkill']
                                    data_dict['clutch_won'] = player_data['clutch_won']
                                    data_dict['survived'] = player_data['survived']
                                    data_dict['trade'] = player_data['trade']
                                    data_dict['flash_assist'] = player_data['flash_assist']
                                    data_dict['adr'] = player_data['adr']
                                    data_dict['isDoubleRatingPoints'] = player_data['isDoubleRatingPoints']
                                    break
                            if 'Damage' in data_dict:
                                break

                        data_list.append(data_dict)

    df = pd.DataFrame(data_list)
    df.to_csv('gamersclub_stats.csv', index=False)
    progress_label.config(text="Estatísticas salvas no arquivo 'gamersclub_stats.csv'")

# Create the GUI window
root = tk.Tk()
root.title("GamersClub Stats")

# Set the window size
window_width = 400
window_height = 300
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_position = int((screen_width / 2) - (window_width / 2))
y_position = int((screen_height / 2) - (window_height / 2))
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

# Center align the window contents
root.grid_columnconfigure(0, weight=1)

# Set the background color
root.configure(bg="#222222")

# Set the default font
default_font = tkfont.nametofont("TkDefaultFont")
default_font.configure(family="Helvetica", size=10, weight="bold")  # Set the weight to "bold"

gclubsess_label = tk.Label(root, text="Insira seu gclubsess:", bg="#222222", fg="white", font=default_font)
gclubsess_label.grid(row=1, column=0, pady=(20, 0))

entry_frame = tk.Frame(root, bg="#222222")
entry_frame.grid(row=2, column=0, pady=(0, 5))

entry = tk.Entry(entry_frame, bg="#333333", fg="white", font=default_font)
entry.pack()

start_year_label = tk.Label(root, text="Insira o ano de início:", bg="#222222", fg="white", font=default_font)
start_year_label.grid(row=3, column=0, pady=(10, 0))

start_year_entry = tk.Entry(root, bg="#333333", fg="white", font=default_font)
start_year_entry.grid(row=4, column=0, pady=(0, 10))

run_loop_var = IntVar()
run_loop_checkbox = tk.Checkbutton(root, text="+estatísticas (leva mais tempo)", variable=run_loop_var, bg="#222222", fg="white", selectcolor="#222222", font=default_font)
run_loop_checkbox.grid(row=5, column=0, pady=(10, 5))

# Create fetch button
fetch_button = tk.Button(root, text="Obter dados", command=fetch_results, bg="#333333", fg="white", activebackground="#555555", activeforeground="white", font=default_font)
fetch_button.grid(row=6, column=0, pady=(10, 5))

# Create progress label
progress_label = tk.Label(root, text="", anchor="center", bg="#222222", fg="white", font=default_font)
progress_label.grid(row=7, column=0, pady=(10, 5))

# Run the GUI event loop
root.mainloop()
