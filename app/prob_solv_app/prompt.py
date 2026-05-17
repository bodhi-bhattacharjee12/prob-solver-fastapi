# List of the prompts which will be used in the nodes
from ast import List
from langchain_core.prompts import ChatPromptTemplate   
from langchain_core.messages import HumanMessage,SystemMessage

classifier_prompt = ChatPromptTemplate.from_messages([
            ("system", "Classify the problemas 'math' or 'writing'. Do not return other than 'math' or 'writing', as it will be used for routing. If you are detecting the problem other than 'math' or 'writing', classify it as 'writing', then identify it as writing."),
            ("user", "{query}")
        ])

def get_planner_prompt(category: str, profile: str) -> str:
    system_msg =  f"You are an expert special education teacher. The student has the following disability: {profile}. Break the {category} task or problem provided in user query into simple steps, so that the specifically tailored for the disability {profile} student is able to solve the problem by his/her own. Do, not provide the solution along with the steps you have broken. It's student's task to solve the steps. Return the steps as a list."
    system_msg+=  f"\n\nIMPORTANT: You are a structural planner, not a chatbot. "
    system_msg+=  f"You MUST calls the 'StepPlan' tool to return the steps. "
    system_msg+=  f"Do not write any text outside the tool call."
    if category == "math":
        system_msg += " For a math problem, lists the calculation steps logically. Do not miss any steps. Do not miss to provide any number or information which is necessary to solve the problem."
    else:
        system_msg += " For writing, list the outline points to cover. Do not miss any important points necessary to write a good piece. Do not create more than three(3) points. Maintain the limitation strictly."

    return system_msg

def get_summery_prompt(steps:list,correct_ans:list) -> str:
    return f"Summarize the lesson we just finished based on these steps: {steps} and the correct answers {correct_ans}. Provide a concise summary highlighting the key points covered and any important takeaways for the student. Also, give positive feedback to the student for their effort and progress. In the end do not forget to mention that we have finally finished the lesson or the problem." 
    
def get_student_prompt(category:str,step: str,prev_steps: list, correct_answers: list) -> list:
    if category == "math":
        question_prompt = f"Ask the student to solve for the problem: {step}. Provide a small hint if necessary to support the student. To solve this step you may need previous steps and the correct answers from the previous stesp. While crafting the question for the student carefully collect the information from the previous steps and the correct answers from the previous steps. The previous steps and the correct answers for the previous steps are provided in the lists: '{prev_steps}','{correct_answers}'."
        return_list = [SystemMessage(content="You are a supportive teacher."), HumanMessage(content=question_prompt)]
    else:  # writing
        question_prompt = f"Ask the student to write some information for the writing task: {step}. Provide a small hint if necessary to support the student. The answers for the previous steps are provided in the list: '{correct_answers}'. While crafting the question please mention the char limit should be less tha 400."
        return_list = [SystemMessage(content="You are a supportive teacher."), HumanMessage(content=question_prompt)]
    return return_list

def get_validation_prompt(category:str, student_answer: str, current_step: str) -> list:

    if category == "math":
        system_prompt = "You are a math validator. Evaluate the student's answer based on the current step."
        validation_prompt = f"""
            Context: The student is working on step: "{current_step}".
            The Student's answer: "{student_answer}".
            
            Is the student's answer correct regarding the current step? 
            Respond with exactly 'CORRECT' or 'INCORRECT' followed by a separator '||' and then provide the explanation why your answer is correct or incorrect.
            Example: INCORRECT||That's close, but try adding 5.
            """
        return [SystemMessage(content=system_prompt+validation_prompt)]
    else:  # writing validation
        system_prompt = "You are a validator. Evaluate the student's answer based on the current step."
        validation_prompt = f"""
                Context: The student is working on step: "{current_step}".
                The Student's answer: "{student_answer}".
                
                Is the student's answer correct regarding the current step? 
                Respond with exactly 'CORRECT' or 'INCORRECT' followed by a separator '||' and then rewrite the student's answer to improve it according to the current step so that, student can gain knowledge how to write it better next time. Note, the ans you will provide that should not be more than 400 characters. Maintain the character limitation strictly. If the answer is correct then do not forget to greet the student.
                Example: INCORRECT||That's close, but try adding 5.
                """
        return [SystemMessage(content=system_prompt+validation_prompt)]

def get_ans_from_teacher_prompt(category:str, student_profile: str, current_step_content: str, prev_steps: list, correct_answers: list) -> str:
    if category == "math":
        return f"Provide the correct answer for the math step: '{current_step_content}'. While calculating the current step you may need the previous steps and the correct answers for the previous steps. The previous steps and the correct answers for the previous steps are provided in the lists: '{prev_steps}','{correct_answers}'."
    else:
        return f"Provide the correct answer for the writing step: '{current_step_content}'. Validate the '{current_step_content}' carefully and based on the student profile {student_profile} decide within how many words the content should be created. Based on your judgement provide the answer. While creating the content for the current step you may need the previous steps and the correct answers for the previous steps. The previous steps and the correct answers for the previous steps are provided in the lists: '{prev_steps}','{correct_answers}'."
