from dotenv import dotenv_values
from second_brain import second_brain
config = dotenv_values(".env")


if __name__ == "__main__":
    sb = second_brain(config)
    sb.recur_task() 
    sb.update_task_kanban_state()