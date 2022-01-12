### Developed by Armand Siorak <asiorak@paloaltonetworks.com> - January 2022
### ALPHA version

""" Get LicenseUsage """


from pc_lib import pc_api, pc_utility
import math
import json

# --Configuration-- #

parser = pc_utility.get_arg_parser()
parser.add_argument(
    '--cloud_account_group_name',
    type=str,
    help='Deprecated - Name of the Cloud Account Group to inspect.')
args = parser.parse_args()

# --Initialize-- #

settings = pc_utility.get_settings(args)
pc_api.configure(settings)
total_credits_consumed = 0
total_others_cloudtype = 0

# --Main-- #

# print('API - Getting the current list of Cloud Account Groups ...', end='')
cloud_account_groups_list = pc_api.cloud_account_group_list_read()
# print(' done.')

# TO DELETE
# cloud_account_group = None
# for item in cloud_account_groups_list:
#     if item['name'] == args.cloud_account_group_name:
#         cloud_account_group = item
#         break

#Looping for each Account Group
for cloud_account_group in cloud_account_groups_list:
	if not cloud_account_group:
	    pc_utility.error_and_exit(400, "Cloud Account Group (%s) not found." % args.cloud_account_group_name)

	if not cloud_account_group['accounts']:
	    # pc_utility.error_and_exit(400, "No Cloud Accounts in Account Group Group (%s)." % cloud_account_group['name'])
	    print("Skipping -- No Cloud Accounts in Account Group (%s)." % cloud_account_group['name'])
	    print()
	    continue

	cloud_account_ids = [cloud_account['id'] for cloud_account in cloud_account_group['accounts']]
	body_params = {
	    'accountIds': cloud_account_ids,
	    'timeRange': {'type':'relative', 'value': {'unit': 'month', 'amount': 1}}
	}

	# print('API - Getting the Usage for Cloud Account Group (%s) ...' % cloud_account_group['name'], end='')
	cloud_account_usage = pc_api.resource_usage_over_time(body_params=body_params)
	total_purchased = cloud_account_usage.get('workloadsPurchased')
	# print(' done.')


	#Get Cloud types
	clouds = cloud_account_usage['dataPoints'][0]['counts'].keys()
	#Get total number of datapoints (used later for average calculation)
	datapoints_size = len(cloud_account_usage['dataPoints'])

	#Initializing dict of dict by looping the results // Creating indexes (might be another method but I am n00b :-) 
	#Retrieve all cloud types and all asset types from the datapoints
	resource_total = {}
	#Get cloud types
	for c in clouds:
		resource_total[c] = {}

		# TO DELETE
		# for asset_type in cloud_account_usage['dataPoints'][0]['counts'][c].keys():
		# 	resource_total[c][asset_type] = 0

		#Get Asset types
		for k in cloud_account_usage['dataPoints']:
			for asset_type in k['counts'][c]:
				resource_total[c][asset_type] = 0

	#Additioning all the credits per cloud per asset types (ex: instances on aws, sql server on azure..)
	for data_points in cloud_account_usage['dataPoints']:
		for k in clouds:
			for t in data_points['counts'][k]:
				resource_total[k][t] += data_points['counts'][k][t]
	

	#Calculating the average. Rounding down each number
	total_per_cloud = {}
	for c in resource_total.keys():
		total_per_cloud[c] = 0
		for at in resource_total[c].keys():
			resource_total[c][at] = int(math.floor(resource_total[c][at]/datapoints_size))
			total_per_cloud[c] += resource_total[c][at]

		if c != "others":
			total_credits_consumed += total_per_cloud[c]

	total_others_cloudtype= total_per_cloud["others"]


	#Print results for the Account Group, excluding "Others" Cloud Type which is not related to any onboarded Cloud Accounts
	print("###################################")
	print("Total for " + cloud_account_group['name'])
	print("###################################")
	print()
	print("Summary:")
	total_per_cloud.pop("others",None)
	print(json.dumps(total_per_cloud, sort_keys=True, indent=2))
	print()
	print("Details:")
	resource_total.pop("others",None)
	print(json.dumps(resource_total,sort_keys=True, indent=2))
	print()


#Print the overall results (Consumed vs Purchased credits)
header = '-' * 40
avg = "TYPE"
prc_c = "USED"
prc_p = "PURCH"
print(header)
print('{:<17s}{:>10s}{:>12s}'.format(avg, prc_c, prc_p))
print(header)
print('{:<17s}{:>10d}{:>12d}'.format("Cloud Accounts", int(total_credits_consumed), int(total_purchased)))
print('{:<17s}{:>10d}{:>12d}'.format("+ Others", int(total_credits_consumed+total_others_cloudtype), int(total_purchased)))
print()
