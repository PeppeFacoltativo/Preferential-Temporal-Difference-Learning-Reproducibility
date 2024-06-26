import numpy as np
import gym
import pickle

from argparse import ArgumentParser

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from collector import dataCollector
from train_traces import trainer
from test import test

parser = ArgumentParser(description="Parameters for the code - gated trace")
parser.add_argument('--trace_type', type=str, default="gated", help="gated or accumulating" )
parser.add_argument('--gamma', type=float, default=0.99, help="discount factor")
parser.add_argument('--n', type=int, default=8, help="chain length")
parser.add_argument('--t_seeds', type=int, default=25, help="total seeds")
parser.add_argument('--env', type=str, default="gridWorld", help="Environment")
parser.add_argument('--intrst', type=float, default=0.01, help="interest of states while using etd")
parser.add_argument('--hidden', type=int, default=1, help="number of hidden units")
parser.add_argument('--test_every', type=int, default=1, help="calculate MSE after # episode")
parser.add_argument('--episodes', type=int, default=30, help="number of episodes")
parser.add_argument('--lr', type=float, default=0.01, help="learning rate")
parser.add_argument('--log', type=int, default=1, help="compute the results")
parser.add_argument('--save', type=int, default=1, help="save the results")
parser.add_argument('--fo', action='store_true', help="type of env")
args = parser.parse_args()

total_seeds = args.t_seeds

seed_errors = []
for seed in range(total_seeds):
	args.seed = seed
	np.random.seed(args.seed)
	torch.manual_seed(args.seed)
	torch.backends.cudnn.deterministic = True
	torch.backends.cudnn.benchmark = False

	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

	if args.env == "gridWorld":
		from grid_world import gridWorld
		from networks import gridNet

		env = gridWorld(n=args.n, po = not(args.fo))
		val_net = gridNet(n=args.n, hidden=args.hidden)
		val_net.to(device)

	elif args.env == "gridWorld2":
		from grid_world2 import gridWorld2
		from networks import gridNet

		env = gridWorld2(n=args.n, po = not(args.fo))
		val_net = gridNet(n=args.n, hidden=args.hidden)
		val_net.to(device)

	elif args.env == "lightWorld":
		from light_world import lightWorld
		from networks import lightNet

		env = lightWorld(n=args.n)
		val_net = lightNet(n=args.n)
		val_net.to(device)

	env.seed(args.seed)

	fname_data = "drl_env_"+str(args.env)+"_size_"+str(args.n)+"_seed_"+str(seed)+"_epi_250"
	with open("data/"+fname_data+"_data.pkl", "rb") as f:
		print(f)
		data_list = pickle.load(f)
	optimizer = optim.SGD(val_net.parameters(), lr=args.lr)
	train_cls = trainer(args, data_list, val_net, optimizer, device)
	test_cls = test(args, env, np.ones((env.n**2,env.action_space.n))/env.action_space.n, device)
	val_net, error_list = train_cls.train(test_cls)

	seed_errors.append(error_list)

seed_error_mean = np.array(seed_errors).mean(axis=0)
seed_error_std = np.array(seed_errors).std(axis=0)

if args.log == 1 and args.save == 1:	
	if args.trace_type in ["etd", "etd_adaptive"]:
		filename = "drl_online_traces_"+args.trace_type+"_int_"+str(args.intrst)+"_env_"+str(args.env)+"_size_"+str(args.n)+"_hidden_"+str(args.hidden)+"_lr_"+str(args.lr)+"_seeds_"+str(args.t_seeds)+"_epi_"+str(args.episodes)
	else:
		filename = "drl_online_traces_"+args.trace_type+"_env_"+str(args.env)+"_size_"+str(args.n)+"_hidden_"+str(args.hidden)+"_lr_"+str(args.lr)+"_seeds_"+str(args.t_seeds)+"_epi_"+str(args.episodes)
	
	with open("results_"+str(args.env)+"/"+filename+"_errors_mean.pkl", "wb") as f:
		pickle.dump(seed_error_mean, f)

	with open("results_"+str(args.env)+"/"+filename+"_errors_std.pkl", "wb") as f:
		pickle.dump(seed_error_std, f)