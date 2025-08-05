// Main application JavaScript
console.log('BrainSAIT LINC Agents - Web Interface Loaded');

// Simple agent status checker
async function checkAgentStatus() {
    const agents = [
        { name: 'Master LINC', port: 8000 },
        { name: 'Auth LINC', port: 8001 },
        { name: 'Doctor LINC', port: 8010 },
        { name: 'Nurse LINC', port: 8011 },
        { name: 'Patient LINC', port: 8012 },
    ];

    for (const agent of agents) {
        try {
            const response = await fetch(`http://localhost:${agent.port}/health`);
            console.log(`${agent.name}: ${response.ok ? 'Healthy' : 'Unhealthy'}`);
        } catch (error) {
            console.log(`${agent.name}: Offline`);
        }
    }
}

// Check agent status on load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Checking agent status...');
    checkAgentStatus();
});