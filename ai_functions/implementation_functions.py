from django.shortcuts import render, redirect
import json
from openai import OpenAI

OPENAI_KEY = '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'
client = OpenAI(api_key=OPENAI_KEY )

MODEL = "gpt-4o-mini"
SYSTEM_DEFAULT_PROPMT_CONTENT = "You are a helpful assistant to ensure ISO 9001:2015 compliance in a manufacturing company. Your answers should be professional, in spanish, concise, and based only on your knowledge about the norm and the following data:\n\n"
MAX_TOKENS_DEFAULT = 250


def ai_text_function(data_input, user_input, max_tokens):
    response = client.chat.completions.create(
        model= MODEL,
        #max_tokens= MAX_TOKENS_DEFAULT,
        messages=[
            {"role": "system", "content": SYSTEM_DEFAULT_PROPMT_CONTENT + f"{data_input}"},
            {"role": "user", "content": user_input}
        ]
    )
    assistant_answer = response.choices[0].message.content
    return assistant_answer

ai_text_function.__doc__ = (
    "This function calls the OpenAI ChatGPT API for a given data_input and user_input.\n"
    "'data_input' must have this format if the data is taken from a database table:\n"
    "data_input = f\"Short description of the data: {data as dict}\"\n"
    "The HTML context should have 'user_input' and 'history' fields.\n"
    "'user_input' should be collected from context using request.POST method before calling this function"
)


def ai_get_conversation_history_function(request,data_input):
    if 'history' not in request.session:    
        history = [
            {"role": "system", "content": SYSTEM_DEFAULT_PROPMT_CONTENT + f"{data_input}"}
        ]
        request.session['history'] = history
        request.session.modified = True
    else:
        history = request.session['history'] 
    
    return history


def ai_conversation_function(request, data_input, user_input):
    history = ai_get_conversation_history_function(request,data_input)
    history.append({
        "role": "user",
        "content": user_input
    })

    response = client.chat.completions.create(
        model= MODEL,
        max_tokens= MAX_TOKENS_DEFAULT,
        messages=history
        )

    assistant_answer = response.choices[0].message.content

    history.append({
        "role": "assistant",
        "content": assistant_answer
    })

    request.session['history'] = history
    request.session.modified = True

    return [history, assistant_answer, user_input]
    

def ai_conversation_delete_function(request, redirect_view):  
    del request.session['history']
    del request.session['user_input']
    request.session.modified = True
    return redirect(redirect_view)

ai_conversation_delete_function.__doc__ = (
    "This function deletes the history of a user-assistant conversation and redirects to a given view.\n"
    "'redirect_view' must have this format:\n 'app_of_the_view_name:view_name'\n"
    "Html context should have 'user_input' and 'history' fields."
)


def ai_json_function(data_input,user_input,json_schema_input,json_function_name,json_function_description):
    response = client.responses.create(
        model= MODEL,
        input=[
            {"role": "system", "content": SYSTEM_DEFAULT_PROPMT_CONTENT + f"{data_input}"},
            {"role": "user", "content": user_input}
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": json_function_name,
                "description": json_function_description,
                "schema": json_schema_input 
                }
            }
    )

    assistant_answer = json.loads(response.output_text)
    return assistant_answer


ai_json_function.__doc__ = (
    "This function returns an AI answer in JSON format.\n"
    "The 'json_schema_input' must have the following structure:\n\n"
    "{\n"
    "    \"type\": \"object\",\n"
    "    \"properties\": {\n"
    "        \"field1\": {\n"
    "            \"type\": \"field1type\",\n"
    "            \"description\": \"Description of the field1\"\n"
    "        },\n"
    "        \"field2\": {\n"
    "            \"type\": \"field2type\",\n"
    "            \"description\": \"Description of the field2\"\n"
    "        }\n"
    "    },\n"
    "    \"required\": [\"field1\", \"field2\"],\n"
    "    \"additionalProperties\": False,\n"
    "    \"strict\": False or True\n"
    "}"
    "For additional info about types (string, number, boolean...), additionalProperties and more, visit: https://platform.openai.com/docs/guides/structured-outputs?api-mode=responses"
)

