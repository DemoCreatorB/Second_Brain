import datetime
import json
import requests
from notion_client import Client, APIErrorCode, APIResponseError

class second_brain():
    def __init__(self, config):
        self.config = config
        self.notion = Client(auth=self.config.get('NOTION_TOKEN'))
        self.databases = dict()
        self.db_ids = dict()
        self.headers = {
            'Authorization': 'Bearer ' + config.get('NOTION_TOKEN')
            ,'Content-Type': 'application/json'
            ,'Notion-Version': '2022-06-28'
        }
        if self.__search_database() > 0:
            self.__init_database()
        print(self.db_ids)
    def __search_database(self):
        search_database = self.notion.search(**{
            'query': "Searching Database",
            'property': 'object',
            'value': 'database'
        })
        print(str(len(search_database['results'])) +" of databases are found")
        return len(search_database['results'])
    
    def __init_database(self):
        search_database = self.notion.search(**{
            'query': "Searching Database",
            'property': 'object',
            'value': 'database'
        })
        
        with open('db.json', 'w', encoding='utf8') as f:
            json.dump(search_database, f, ensure_ascii=False, indent=4)
        for i in search_database['results']:
            if(i['object']=='database'):
                 self.db_ids.update({i['title'][0]['text']['content']:i['id']})

    def update_task_kanban_state(self):
        if self.db_ids['Tasks Database'] == None:
            return
        print("---updating states---")
        task_database = self.get_database(self.db_ids['Tasks Database']) 
        for task in (task_database.json())['results']:
            if task['properties']['Due']['date'] == None or (task['properties']['Kanban - State']['select'] != None and task['properties']['Kanban - State']['select']['name'] == 'Failed'):
                continue
            elif task['properties']['Done']['checkbox']:
                if task['properties']['Kanban - State']['select'] == None or task['properties']['Kanban - State']['select']['name']!='Done':
                    update_kanban_state = {'Kanban - State':{'type':'select', 'select':{'name':'Done', 'color':'green'}}}
                    print("Done state")
                    self.update_page(task['id'], update_kanban_state)
            elif task['properties']['Due']['date']['end'] != None:
                if (task['properties']['Kanban - State']['select'] == None or task['properties']['Kanban - State']['select']['name']!='Failed') and task['properties']['Due']['date']['end'] != None and datetime.datetime.strptime(task['properties']['Due']['date']['end'][0:10], "%Y-%m-%d") + datetime.timedelta(days=3) < datetime.datetime.today():
                    update_kanban_state = {'Kanban - State':{'type':'select', 'select':{'name':'Failed', 'color':'gray'}}}
                    print("Fail state")
                    self.update_page(task['id'], update_kanban_state)
                elif (task['properties']['Kanban - State']['select'] == None or task['properties']['Kanban - State']['select']['name']!='Late') and task['properties']['Due']['date']['end'] != None and datetime.datetime.strptime(task['properties']['Due']['date']['end'][0:10], "%Y-%m-%d") + datetime.timedelta(days=1) < datetime.datetime.today():
                    update_kanban_state = {'Kanban - State':{'type':'select', 'select':{'name':'Late', 'color':'default'}}}
                    print("Late state-end")
                    self.update_page(task['id'], update_kanban_state)    
            else:
                if (task['properties']['Kanban - State']['select'] == None or task['properties']['Kanban - State']['select']['name']!='Failed') and task['properties']['Due']['date'] != None and datetime.datetime.strptime(task['properties']['Due']['date']['start'][0:10], "%Y-%m-%d") + datetime.timedelta(days=3) < datetime.datetime.today():
                    update_kanban_state = {'Kanban - State':{'type':'select', 'select':{'name':'Failed', 'color':'gray'}}}
                    print("Fail state")
                    self.update_page(task['id'], update_kanban_state)
                elif (task['properties']['Kanban - State']['select'] == None or task['properties']['Kanban - State']['select']['name']!='Late') and task['properties']['Due']['date'] != None and datetime.datetime.strptime(task['properties']['Due']['date']['start'][0:10], "%Y-%m-%d") + datetime.timedelta(days=1) < datetime.datetime.today():
                        update_kanban_state = {'Kanban - State':{'type':'select', 'select':{'name':'Late', 'color':'default'}}}
                        print("Late state-start")
                        self.update_page(task['id'], update_kanban_state)

    def recur_task(self):
        if self.db_ids['Tasks Database'] == None:
            return
        print("---recurring tasks---")
        task_database = self.get_database(self.db_ids['Tasks Database']) 
        # with open('db.json', 'w', encoding='utf8') as f:
        #     json.dump(task_database.json(), f, ensure_ascii=False, indent=4)
        
        parent_recur_tasks = list()
        child_recur_tasks = list()
        for task in (task_database.json())['results']:
            if task['properties']['Due']['date'] == None:
                pass 
            elif task['properties']['Due']['date']['end'] != None:
                if task['properties']['Due']['date']['end'] == (datetime.datetime.today()).strftime("%Y-%m-%d") and task['properties']['Recur Interval']['number'] != None and not task['properties']['Recur Done']['checkbox']:    
                    print(task['properties']['Task']['title'][0]['text']['content'])
                    parent_recur_tasks.append(task['properties'])
            else:
                if task['properties']['Due']['date']['start'] == (datetime.datetime.today()).strftime("%Y-%m-%d") and task['properties']['Recur Interval']['number'] != None  and not task['properties']['Recur Done']['checkbox']:
                    print(task['properties']['Task']['title'][0]['text']['content'])
                    parent_recur_tasks.append(task)
        
        for task in parent_recur_tasks:
            temp = dict()
            temp.update({'Task': {'type':'title','title':[{'type':'text', 'text':{'content':task['properties']['Task']['title'][0]['text']['content'], 'link':None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default"
                            },'plain_text':task['properties']['Task']['title'][0]['plain_text']}]}})
            temp.update({'Due':{'date':{'start':(datetime.datetime.strptime(task['properties']['Next Due']['formula']['string'], "%B %d, %Y")).strftime("%Y-%m-%d")}}})
            temp.update({'Recur Unit':{'type':'select', 'select':{'name':task['properties']['Recur Unit']['select']['name'], 'color':task['properties']['Recur Unit']['select']['color']}}})
            temp.update({'Recur Interval':{'type':'number', 'number':task['properties']['Recur Interval']['number']}}) 
            temp.update({'Priority':{'type':'select', 'select':{'name':task['properties']['Priority']['select']['name'], 'color':task['properties']['Priority']['select']['color']}}})
            temp.update({'Kanban - State':{'type':'select', 'select':{'name':'To Do', 'color':'red'}}})
            if task['properties']['Days (Only if Set to 1 Day(s))']['select'] != None:
                temp.update({'Days (Only if Set to 1 Day(s))': {'type':'select', 'select':{'name':task['properties']['Days (Only if Set to 1 Day(s))']['select']['name'], 'color':task['properties']['Days (Only if Set to 1 Day(s))']['select']['color']}}})
            child_recur_tasks.append(temp)
            update_recur_done = {'Recur Done':{'checkbox':True}}
            self.update_page(task['id'], update_recur_done)


        
        for task in child_recur_tasks:
             self.create_page(self.db_ids['Tasks Database'], task)
    
    def get_database(self, db_id:str, pl:int=100):
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        payload = {'page_size': pl}
        return requests.post(url, json=payload, headers=self.headers)

    def create_page(self, db_id:str, data:dict):
        create_url = "https://api.notion.com/v1/pages"
        payload={'parent':{'database_id':db_id}, "properties":data}
        res = requests.post(create_url, headers=self.headers, json=payload)
        print(res.status_code)

    def update_page(self, page_id:str, data:dict):
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        payload={"properties":data}
        res = requests.patch(update_url, headers=self.headers, json=payload)
        print(res.status_code)