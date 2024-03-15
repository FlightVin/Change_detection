import pickle
import numpy as np

file_path = "/scratch/vineeth.bhat/results/8-room-new-FourDNet/results.pkl"

with open(file_path, "rb") as f:
    data = pickle.load(f)

trans_errs = []
rot_errs = []

for i in range(len(data['translation_errors'])):
    print("Translation error", data['translation_errors'][i])
    print("Rot error", data['rotation_errors'][i])
    print("Assgn", data['assignments'][i][0])

    if len(data['assignments'][i][0]) > 0: # since our method is only valid if objects exist in our query frame
        trans_errs.append(data['translation_errors'][i])
        rot_errs.append(data['rotation_errors'][i])

trans_errs = np.array(trans_errs)
rot_errs = np.array(rot_errs)


print("Trans rmse", np.sqrt(np.mean(trans_errs ** 2)))
print("Rot rmse", np.sqrt(np.mean(rot_errs ** 2))) 

