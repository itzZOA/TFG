import openai
import os

openai.api_key = "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"
openai.organization = "org-OB4THAkEBAWQWhxKZhodli7j"

conversation = ""
i=1
while (i!=0):
    question = input("Human: ")
    conversation += "\nHuman: " + question + "\nAI:"
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=conversation,
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"]
    )

    answer = response.choices[0].text.strip()
    conversation += answer
    print ("AI: " + answer + "\n")

