import sqlite3
import pandas as pd
import re

from shiny import reactive
from shiny.express import render, ui, input



# creates the database bysykkel
with open('bysykkel.sql', 'r', encoding='utf8') as sql_file:
    sql_script = sql_file.read()

con = sqlite3.connect(':memory:')
cur = con.cursor()
_ = cur.executescript(sql_script)


with ui.card():
    ui.card_header("Task 1")
    
    with ui.card():
        ui.card_header("a)")
        #--- Write your solution to 1a here ---

        #Could print it to the site with putting the strings inside '''  Name, student_id   '''
        #But it is most probably best practice to use the render methods
        
        @render.text
        def print_name_id():
            return 'ei1000, 111111'


    with ui.card():
        ui.card_header("b)")
        #--- Write your solution to 1b here ---

        #Input texts, with placeholders for quick testing. And the button
        ui.input_text('name', 'Name:', 'Ola Nårdmann')
        ui.input_text('mail', 'Mail:', 'Ola.nårdman@norskmail.com')
        ui.input_text('phone_num', 'Phone number:', '12345678')
        ui.input_action_button("submit", "Submit", class_="btn-success")

        @render.code
        @reactive.event(input.submit, ignore_none=True)
        def print_names():
            return f'{input.name.get()} \n{input.mail.get()} \n{input.phone_num.get()}'
        
        
        
    with ui.card():
        ui.card_header("c)")
        #--- Write your solution to 1c here ---

        #Done with and without regex. Figured since it was imported in the file, that it was preferred

        #Creating a simple function that takes a string and condition. If the condition is true -> valid.
        def valid_or(input_string, condition):
            if condition:
                return input_string + ' - Valid'
            else:
                return input_string + ' - Not Valid'

        #Create the norwegian alphabet
        alphabet = set('abcdefghijklmnopqrstuvwxyzæøå')

        

        #Render if the inputs are valid or not when the submit button is pressed
        @render.code
        @reactive.event(input.submit, ignore_none=True)
        def print_names_valid():
            
            #Alternatively set(input.name.get().lower().replace(" ", "")).issubset(alphabet)
            name = valid_or(input.name.get(), bool(re.match('^[a-æøåA-ÆØÅ]+$', input.name.get().replace(" ", ""))))

            
            #Check if @ is in the mail. Alternatively use '@' in input.mail.get().strip()
            mail = valid_or(input.mail.get(), bool(re.findall('@', input.mail.get())))
            

            #Check the lenght of the number. Or use len(input.phone_num.get()) == 8
            phone = valid_or(input.phone_num.get(), re.match('^[0-9]{8}$', input.phone_num.get()))
            

            #Return the code with newlines
            return f'{name} \n{mail} \n{phone}'
        

with ui.card():
    ui.card_header("Task 2")
    
    with ui.panel_well():
        ui.card_header("a)")
        #--- Write your solution to 2a here ---
        @render.table
        def rndr_stations():
            return pd.read_sql_query("SELECT name from users ORDER BY name;", con)
        
        
        

    with ui.panel_well():
        ui.card_header("b)")
        #--- Write your solution to 2b here ---
        @render.table
        def rndr_bikes():
            return pd.read_sql_query("SELECT name, status from bikes;", con)
        
        
    with ui.panel_well():
        ui.card_header("c)")
        #--- Write your solution to 2c here ---

        @render.table
        def rndr_subs():
            
            #Simple groupby query, and count the repeating rows
            return pd.read_sql_query('SELECT type, COUNT(*) as Purchased from subscriptions GROUP BY type', con)
        
        
with ui.card():
    ui.card_header("Task 3")
    
    with ui.panel_well():
        ui.card_header("a)")
        #--- Write your solution to 3a here ---

        #Input text and press filter button
        ui.input_text('users', 'User filter', 'HAN')
        ui.input_action_button("filter", "Search", class_="btn-success")

        @render.data_frame
        @reactive.event(input.filter)
        def result():
            #Thanks to discord for pointing out that 0 cannot be a leading number. Easy solution. 
            return pd.read_sql_query("SELECT user_id, name, printf('%08d',phone_number) as 'Phone number' from users WHERE name LIKE ?;", con, params=['%'+input.users()+'%'])

    with ui.panel_well():
        ui.card_header("b)")
        #--- Write your solution to 3b here ---
        
        #Grouping on endstations, and joining trips and stations to get the name

        @render.data_frame
        def rndr_station_end():
            sub_types = pd.read_sql_query('''SELECT end_station as station_id, stations.name as Name, COUNT(end_station) as Trips 
                                          FROM trips JOIN stations ON stations.station_id = trips.end_station GROUP BY end_station;''', con)
      
            return sub_types
        
    with ui.panel_well():
        ui.card_header("c)")
        #--- Write your solution to 3c here ---

        #Had some trouble putting strings in params in pd.read_sql_query. So I came across .format(). Was easy to implement with. 
        #https://stackoverflow.com/questions/36840438/binding-list-to-params-in-pandas-read-sql-query-with-other-params

        #General solution
        years = []
        for x in cur.execute("SELECT strftime('%Y', start_time) from subscriptions").fetchall():
            if x[0] not in years:
                years.append(x[0])
        
        def case_year(year_list):
            str_output = ''
            for year in year_list:
                if year is year_list[-1]:
                    str_output += f"SUM(CASE WHEN strftime('%Y', start_time) = '{year}' THEN 1 ELSE 0 END) as '{year}'"
                else:
                    str_output += f"SUM(CASE WHEN strftime('%Y', start_time) = '{year}' THEN 1 ELSE 0 END) as '{year}',\n"
            
            query_part = '''SELECT users.user_id, users.name, 
                    {}
                    from subscriptions JOIN users ON users.user_id  = subscriptions.user_id
                    GROUP BY users.user_id
                    ;'''.format(str_output)

            return query_part


        #The more general solution if there are more years in another version of the database.
        @render.data_frame
        def rndr_users_sub_gen():
            sub_types = pd.read_sql_query(case_year(sorted(years)), con)
            
            #print(counting_stations)
            return sub_types
        
        

        #More hardcoded, incase the general solution has a bug.
        #@render.data_frame
        def rndr_users_sub():
            sub_types = pd.read_sql_query(f'''SELECT users.user_id, users.name, 
                                          SUM(CASE WHEN strftime('%Y', start_time) = '2018' THEN 1 ELSE 0 END) as '2018',
                                          SUM(CASE WHEN strftime('%Y', start_time) = '2019' THEN 1 ELSE 0 END) as '2019',
                                          SUM(CASE WHEN strftime('%Y', start_time) = '2020' THEN 1 ELSE 0 END) as '2020',
                                          SUM(CASE WHEN strftime('%Y', start_time) = '2021' THEN 1 ELSE 0 END) as '2021'
                                          
                                          
                                          from subscriptions JOIN users ON users.user_id  = subscriptions.user_id
                                          GROUP BY users.user_id
                                        

                                          ;''', con)
            

            
            #print(counting_stations)
            return sub_types
        
        
with ui.panel_well():
    ui.card_header("Task 4")
    #--- Write your solution to 4 here ---
    stations = [ x[0] for x in cur.execute('SELECT name from stations').fetchall()]
    ui.input_selectize('stasjon', 'Station:', stations)
    ui.input_switch('trip_switch', 'Active trip')
    #print(input.stasjon())
    @render.table(render_links=True, escape=False)
    @reactive.event(input.stasjon, input.trip_switch, ignore_none=True)
    def rndr_availability():
        
        #Were getting all 0 at first. Figured it was because the columns are declared as INT in the sql file. 
        #Read the documentation and stackoverflow, found that you could multiply one number with a float or cast it as a float
        #I have tried to search for what is best practice but it seems to not have a clear answer.
        #In my opinion multiplying by float is shorter and more readable. If it however is more expensive to run, then I would use cast instead.
        #Also found that converting float to int uses floor() : https://stackoverflow.com/questions/7129249/getting-the-floor-value-of-a-number-in-sqlite
        #Therefore I need to use round() to round up.
        #Found how to add the percentage sign on: https://database.guide/2-ways-to-add-a-percent-sign-to-a-number-in-sqlite/
        #FORMAT was the easiest since it got rid of the decimal places too. 

        if input.trip_switch():
            #If on bike
            formula = "FORMAT('%1d%%',ROUND(1.0 * available_spots / max_spots *100))"
            #"FORMAT('%5d%%',ROUND(CAST(available_spots as FLOAT) / max_spots *100))"
            
        else:
            #If on foot
            formula = "FORMAT('%1d%%', ROUND(1.0*(max_spots - available_spots) / max_spots *100))"
        
        #Found out that you can connocate with || ||. So made the other parts of the link to a string, so that latitude and longitude would be from the columns.
        query = '''SELECT name,{0}as Availability,
        '<a href=https://www.google.com/maps?q='||latitude||','||longitude||'>Link</a>' as link
        from stations where name = {1}'''.format(formula, '?')


        return pd.read_sql_query(query, con, params=[input.stasjon()])

with ui.panel_well():
    ui.card_header('END')
