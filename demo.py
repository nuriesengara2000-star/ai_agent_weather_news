from agent import create_agent

def main():
    agent = create_agent()

    print("AI Agent is ready!")
    print("You can ask about weather, news, or currency.")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("YOU: ")

        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break

        try:
            result = agent.invoke({"input": user_input})
            print("AGENT:", result["output"])
        except Exception as e:
            print("Error:", str(e))

if __name__ == "__main__":
    main()