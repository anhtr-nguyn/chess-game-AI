import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
from chess_env import ChessEnv  # Import the modified chess environment with dense rewards

# ----------------------------
# Neural Network for DQN
# ----------------------------
class ChessDQN(nn.Module):
    def __init__(self, input_dim=833, output_dim=4096, hidden_dims=[512, 256]):
        """
        A simple fully-connected network.
        Input:
          - input_dim: size of the state vector (64 squares * 13 features + 1 turn indicator = 833)
          - output_dim: number of possible actions (64 * 64 = 4096)
          - hidden_dims: list of hidden layer sizes
        """
        super(ChessDQN, self).__init__()
        layers = []
        last_dim = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(last_dim, h))
            layers.append(nn.ReLU())
            last_dim = h
        layers.append(nn.Linear(last_dim, output_dim))
        self.model = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.model(x)

# ----------------------------
# Replay Buffer for Experience Replay
# ----------------------------
class ReplayBuffer:
    def __init__(self, capacity=10000):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        state, action, reward, next_state, done = map(np.array, zip(*batch))
        return state, action, reward, next_state, done
    
    def __len__(self):
        return len(self.buffer)

# ----------------------------
# DQN Agent
# ----------------------------
class DQNAgent:
    def __init__(self, input_dim=833, output_dim=4096, hidden_dims=[512,256],
                 lr=1e-4, gamma=0.99, device=torch.device("cpu")):
        self.device = device
        self.policy_net = ChessDQN(input_dim, output_dim, hidden_dims).to(device)
        self.target_net = ChessDQN(input_dim, output_dim, hidden_dims).to(device)
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.gamma = gamma
        self.update_target()  # Initialize target network
        self.steps_done = 0
    
    def update_target(self):
        """Copy the policy network weights into the target network."""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def select_action(self, state, valid_actions, epsilon):
        """
        Choose an action using an epsilon-greedy policy over valid actions.
        - state: current state as a numpy array.
        - valid_actions: list of action indices corresponding to legal moves.
        - epsilon: exploration rate.
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        if random.random() < epsilon:
            return random.choice(valid_actions)
        else:
            with torch.no_grad():
                q_values = self.policy_net(state_tensor).cpu().data.numpy().flatten()
            # Only consider valid actions
            valid_q = [(action, q_values[action]) for action in valid_actions]
            best_action = max(valid_q, key=lambda x: x[1])[0]
            return best_action
    
    def optimize_model(self, replay_buffer, batch_size):
        if len(replay_buffer) < batch_size:
            return None
        states, actions, rewards, next_states, dones = replay_buffer.sample(batch_size)
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.device)
        
        # Compute Q(s,a) for the current state
        current_q = self.policy_net(states).gather(1, actions)
        # Compute max Q-value for next state from target network
        with torch.no_grad():
            max_next_q = self.target_net(next_states).max(1)[0].unsqueeze(1)
            target_q = rewards + self.gamma * max_next_q * (1 - dones)
        
        loss = nn.MSELoss()(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return loss.item()

# ----------------------------
# Training Loop
# ----------------------------
def train_dqn(num_episodes=1000, batch_size=64, target_update=10,
              epsilon_start=1.0, epsilon_end=0.1, epsilon_decay=0.995):
    env = ChessEnv()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent = DQNAgent(device=device)
    replay_buffer = ReplayBuffer(capacity=10000)
    epsilon = epsilon_start
    episode_rewards = []
    
    for i_episode in range(num_episodes):
        state = env.reset()
        total_reward = 0.0
        done = False
        
        # Get valid actions for the initial state from the game engine
        valid_moves = env.game.get_valid_moves()
        valid_actions = [env.move_to_action_index(m) for m in valid_moves]
        
        while not done:
            action = agent.select_action(state, valid_actions, epsilon)
            next_state, reward, done, info = env.step(action)
            total_reward += reward
            replay_buffer.push(state, action, reward, next_state, done)
            state = next_state
            
            # Update valid actions based on the new game state
            valid_moves = env.game.get_valid_moves()
            valid_actions = [env.move_to_action_index(m) for m in valid_moves]
            
            agent.optimize_model(replay_buffer, batch_size)
        
        epsilon = max(epsilon_end, epsilon * epsilon_decay)
        episode_rewards.append(total_reward)
        if i_episode % target_update == 0:
            agent.update_target()
        if i_episode % 10 == 0:
            print(f"Episode {i_episode}: Total Reward = {total_reward:.2f}, Epsilon = {epsilon:.2f}")
    
    return agent, episode_rewards

# ----------------------------
# Main Entry Point
# ----------------------------
if __name__ == "__main__":
    trained_agent, rewards = train_dqn(num_episodes=200)
    # Optionally, save the model
    torch.save(trained_agent.policy_net.state_dict(), "chess_dqn_model.pth")
