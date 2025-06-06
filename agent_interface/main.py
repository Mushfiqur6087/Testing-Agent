from flask import Flask, request, jsonify
from agent.main_agent.agent import TestAgent
from controller.browser_controller import BrowserController
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from root .env file
root_dir = Path(__file__).parent.parent
load_dotenv(root_dir / '.env')

app = Flask(__name__)
browser_controller = BrowserController()
test_agent = TestAgent(browser_controller)

@app.route('/api/test/run', methods=['POST'])
def run_test():
    data = request.json
    goal = data.get('goal')
    if not goal:
        return jsonify({'error': 'No goal provided'}), 400
    
    try:
        execution_log = test_agent.execute_plan(goal)
        summary = test_agent.get_session_summary()
        return jsonify({
            'status': 'success',
            'execution_log': execution_log,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/status', methods=['GET'])
def get_status():
    return jsonify(test_agent.get_status())

@app.route('/api/test/results', methods=['GET'])
def get_results():
    return jsonify(test_agent.get_session_summary())

@app.route('/api/test/configure', methods=['POST'])
def configure():
    data = request.json
    try:
        test_agent.configure(**data)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('AGENT_PORT', 5000))
    app.run(host='0.0.0.0', port=port) 