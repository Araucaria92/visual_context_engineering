
import eel
from src.vcer.core.analyzer import analyze_with_gemini, analyze_with_custom_llm

# Initialize Eel with the 'web' folder
eel.init('web')

@eel.expose  # Expose the function to JavaScript
def analyze_semantic_payload(details):
    """A wrapper function to be called from JavaScript that routes to the correct analyzer."""
    try:
        payload = details.get('payload')
        backend = details.get('backend')

        if backend == 'gemini':
            return analyze_with_gemini(payload)
        elif backend == 'custom':
            url = details.get('url')
            model = details.get('model')
            if not url or not model:
                raise ValueError("URL and Model Name are required for custom LLM.")
            return analyze_with_custom_llm(payload, url, model)
        else:
            raise ValueError(f"Unknown backend: {backend}")

    except Exception as e:
        # Return an error object to the frontend
        return {'error': str(e)}

print("Starting desktop application... Close the window to stop.")

# Start the application. Eel will handle creating the window.
# You might need to specify a browser if Chrome is not found.
eel.start('index.html', size=(1200, 800))

print("Application closed.")
