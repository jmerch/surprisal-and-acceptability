
import os, sys, torch, transformers, math, ast
from transformers import AutoTokenizer, AutoModelForCausalLM

preps = ["of", "about", "against", "for", "to", "in", "on"]

def main():
    source = sys.argv[1]
    id_csv = sys.argv[2]
    name = sys.argv[3]
    f = open(source)
    out = open("data/"+name+"_"+"surprisals.csv", "w")
    surps = open("data/individual_surprisals.txt")
    unique_word_surprisal = ast.literal_eval(surps.readlines()[0])
    id_file = open(id_csv)
    raw_types = id_file.readlines()
    raw_types.pop(0)
    id_to_type = {}
    sentence_id = 0
    for i in range(len(raw_types)):
        print(raw_types[i])
        data = raw_types[i].strip().strip('"').split(",")
        id = int(data[0])
        type = data[1][1:]
        id_to_type[id] = type
        if i == 0:
            sentence_id = id
    curr_total = 0
    exp_inc_total = 0
    exp_dec_total = 0
    exp_sum_total = 0
    normal_total = 0
    num_words = 0
    weight_total = 0
    region_total = 0
    region_size = 0
    #gauss_weight_total = 0
    surprisals = []
    words = []
    lines = f.readlines()
    lines.pop(0)
    out.write('"sentence_id","mean_surprisal","weight_first","weight_last","weight_sum","normalized","wh","matrix","comp","embedded","gap","matrix_norm","comp_norm","embedded_norm","gap_norm","beyond_5", "beyond_6", "beyond_7", "beyond_8", "beyond_9"\n')

    '''unique_word_surprisal = {}
    for line in lines:
        data = line.strip().split(" ")
        word = data[0]
        if word not in unique_word_surprisal:
            unique_word_surprisal[word] = 0
    get_individual_surprisal(unique_word_surprisal, "gpt2")
    #print(unique_word_surprisal) '''
    for line in lines:
        data = line.strip().split(" ")
        word = data[0]
        surprisal = float(data[1])
        num_words += 1
        surprisals.append(surprisal)
        words.append(word.lower())
        if (word in '?.' ):
            print(words)
            for i in range(num_words):
                #gauss_weight = math.exp(-(i - (num_words / 2))**2)
                inc_weight = math.exp(-i)
                dec_weight = math.exp(-(num_words - i - 1))
                exp_inc_total += surprisals[i] * inc_weight
                exp_dec_total += surprisals[i] * dec_weight
                exp_sum_total += surprisals[i] * (inc_weight + dec_weight)
                curr_total += surprisals[i]
                #gauss_total += surprisals[i] * gauss_weight
                weight_total += inc_weight
                normal_total += surprisals[i] / get_norm(words[i], unique_word_surprisal)
                #gauss_weight_total += gauss_weight
            wh = wh_norm = matrix = matrix_norm = comp = comp_norm = embedded = embedded_norm = gap = gap_norm = 0
            if (sentence_id in id_to_type) and id_to_type[sentence_id] in ["WH", "CNPC", "SUBJ"]:
                wh = get_wh(words, surprisals)
                wh_norm = get_wh(words, surprisals, unique_word_surprisal)
                matrix = get_matrix(words, surprisals)
                matrix_norm = get_matrix(words, surprisals, unique_word_surprisal)
                comp = get_comp(words, surprisals)
                comp_norm = get_comp(words, surprisals, unique_word_surprisal)
                embedded = get_embedded(words, surprisals)
                embedded_norm = get_embedded(words, surprisals, unique_word_surprisal)
                gap = get_gap(words, surprisals, id_to_type[sentence_id])
                gap_norm = get_gap(words, surprisals, id_to_type[sentence_id], unique_word_surprisal)
            elif (sentence_id in id_to_type):
                gap = get_gap(words, surprisals, id_to_type[sentence_id])
                gap_norm = get_gap(words, surprisals, id_to_type[sentence_id], unique_word_surprisal)
            if gap == None:
                gap = 0
                gap_norm = 0
            out.write(f'{sentence_id},{curr_total / num_words},{exp_inc_total / weight_total},{exp_dec_total / weight_total},{exp_sum_total / (weight_total * 2)},{normal_total / num_words},{wh},{matrix},{comp},{embedded},{gap},{matrix_norm},{comp_norm},{embedded_norm},{gap_norm},{beyond_threshold(words, surprisals, 5)},{beyond_threshold(words, surprisals, 6)},{beyond_threshold(words, surprisals, 7)},{beyond_threshold(words, surprisals, 8)},{beyond_threshold(words, surprisals, 9)}\n')
            sentence_id += 1
            curr_total = 0
            weight_total = 0
            exp_dec_total = 0
            exp_inc_total = 0
            exp_sum_total = 0
            normal_total = 0
            #gauss_weight_total = 0
            num_words = 0
            surprisals = []
            words = []

def get_wh(words, surprisals, normalization_consts = None):
    if normalization_consts == None:
        return surprisals[0]
    return surprisals[0] / get_norm(words[0], normalization_consts)
    return 0

def get_matrix(words, surprisals, normalization_consts = None):
    total = 0
    num_words = len(words)
    region_size = 0
    for i in range(1, num_words):
        if words[i] == 'that' or words[i] == 'whether':
            break
        elif normalization_consts == None:
            total += surprisals[i]
            region_size += 1
        else:
            total += surprisals[i] / get_norm(words[i], normalization_consts)
            region_size += 1
    if region_size == 0:
        return 0
    return total / region_size

def get_comp(words, surprisals, normalization_consts = None):
    num_words = len(words)
    for i in range(1, num_words):
        if words[i] == 'that' or words[i] == 'whether':
            if normalization_consts == None:
                return surprisals[i]
            return surprisals[i] / get_norm(words[i], normalization_consts)
    return 0

def get_embedded(words, surprisals, normalization_consts = None):
    num_words = len(words)
    total = 0
    region_size = 0
    embedded = False
    for i in range(1, num_words):
        if not embedded and (words[i] == 'that' or words[i] == 'whether'):
            embedded = True
            continue
        if embedded:
            if normalization_consts == None:
                total += surprisals[i]
            else:
                total += surprisals[i] / get_norm(words[i], normalization_consts)
            region_size += 1
    if (region_size == 0):
        return 0
    return total / region_size

def get_gap(words, surprisals,  condition, normalization_consts = None):
    if condition in ["FILL", "POLAR"]:
        return 0
    if condition == "UNGRAM":
        return 30
    num_words = len(words)
    if condition in ["WH", "CNPC"] or ".lg" in condition: # "RC.adj.isl.lg", "RC.adj.non.lg"]:
        if (normalization_consts == None):
            return surprisals[-1]
        return surprisals[-1] / get_norm(words[-1], normalization_consts)
    for i in range(1, num_words):
        if words[i] in preps and (condition == "SUBJ" or ".sub." in condition):
            if normalization_consts == None:
                return surprisals[i + 1]
            return surprisals[i + 1] / get_norm(words[i + 1], normalization_consts)
        if words[i] in ["that", "who"] and ".sh" in condition: # in ["RC.adj.non.sh",  "RC.adj.isl.sh"]:
            if normalization_consts == None:
                return surprisals[i + 1]
            return surprisals[i + 1] / get_norm(words[i + 1], normalization_consts)
    return 0

def get_norm(word, normalization_consts):
    if word in normalization_consts:
        return normalization_consts[word]
    return normalization_consts["the"]

def beyond_threshold(words, surprisals, threshold, normalization_consts = None):
    num_beyond = 0
    beyond_total = 0
    for i in range(len(surprisals)):
        if surprisals[i] >= threshold + 8:
            if (normalization_consts == None):
                beyond_total += surprisals[i]
            else:
                beyond_total += surprisals[i] / get_norm(words[i], normalization_consts)
            num_beyond += 1
    if num_beyond > 0:
        return beyond_total / num_beyond
    return 0


def get_individual_surprisal(surprisal_dict, model):
    model_variant = model
    if "gpt-neox" in model_variant:
        tokenizer = GPTNeoXTokenizerFast.from_pretrained(model)
    elif "gpt" in model_variant:
        tokenizer = AutoTokenizer.from_pretrained(model, use_fast=False)
    elif "opt" in model_variant:
        tokenizer = AutoTokenizer.from_pretrained(model, use_fast=False)
    else:
        raise ValueError("Unsupported LLM variant")
    model = AutoModelForCausalLM.from_pretrained(model)
    model.eval()
    softmax = torch.nn.Softmax(dim=-1)
    ctx_size = model.config.max_position_embeddings
    bos_id = model.config.bos_token_id

    for word in surprisal_dict.keys():
        batches = []
        tokenizer_output = tokenizer(word)
        ids = tokenizer_output.input_ids
        attn = tokenizer_output.attention_mask
        start_idx = 0

        # sliding windows with 50% overlap
        # start_idx is for correctly indexing the "later 50%" of sliding windows
        while len(ids) > ctx_size:
            # for GPT-NeoX (bos_id not appended by default)
            if "gpt-neox" in model_variant:
                batches.append((transformers.BatchEncoding({"input_ids": torch.tensor([bos_id] + ids[:ctx_size-1]).unsqueeze(0),
                                                               "attention_mask": torch.tensor([1] + attn[:ctx_size-1]).unsqueeze(0)}),
                                    start_idx))
            # for GPT-2/GPT-Neo (bos_id not appended by default)
            elif "gpt" in model_variant:
                batches.append((transformers.BatchEncoding({"input_ids": torch.tensor([bos_id] + ids[:ctx_size-1]),
                                                                "attention_mask": torch.tensor([1] + attn[:ctx_size-1])}),
                                    start_idx))
            # for OPT (bos_id appended by default)
            else:
                batches.append((transformers.BatchEncoding({"input_ids": torch.tensor(ids[:ctx_size]).unsqueeze(0),
                                                            "attention_mask": torch.tensor(attn[:ctx_size]).unsqueeze(0)}),
                                    start_idx))

            ids = ids[int(ctx_size/2):]
            attn = attn[int(ctx_size/2):]
            start_idx = int(ctx_size/2)-1

        # remaining tokens
        if "gpt-neox" in model_variant:
            batches.append((transformers.BatchEncoding({"input_ids": torch.tensor([bos_id] + ids).unsqueeze(0),
                                                           "attention_mask": torch.tensor([1] + attn).unsqueeze(0)}),
                               start_idx))
        elif "gpt" in model_variant:
                batches.append((transformers.BatchEncoding({"input_ids": torch.tensor([bos_id] + ids),
                                                           "attention_mask": torch.tensor([1] + attn)}),
                               start_idx))
        else:
            batches.append((transformers.BatchEncoding({"input_ids": torch.tensor(ids).unsqueeze(0),
                                                            "attention_mask": torch.tensor(attn).unsqueeze(0)}),
                                start_idx))

        curr_word_ix = 0
        curr_word_surp = []
        curr_toks = ""
        words = [word]
        for batch in batches:
            batch_input, start_idx = batch
            output_ids = batch_input.input_ids.squeeze(0)[1:]

            with torch.no_grad():
                model_output = model(**batch_input)

            toks = tokenizer.convert_ids_to_tokens(batch_input.input_ids.squeeze(0))[1:]
            index = torch.arange(0, output_ids.shape[0])
            surp = -1 * torch.log2(softmax(model_output.logits).squeeze(0)[index, output_ids])

            for i in range(start_idx, len(toks)):
                # necessary for diacritics in Dundee
                cleaned_tok = toks[i].replace("Ġ", "", 1).encode("latin-1").decode("utf-8")

                # for token-level surprisal
                # print(cleaned_tok, surp[i].item())

                # for word-level surprisal
                curr_word_surp.append(surp[i].item())
                curr_toks += cleaned_tok
                # summing subword token surprisal ("rolling")
                words[curr_word_ix] = words[curr_word_ix].replace(cleaned_tok, "", 1)
                if words[curr_word_ix] == "":
                    surprisal_dict[curr_toks] = sum(curr_word_surp)
                    '''print(curr_toks, sum(curr_word_surp))
                    curr_word_surp = []
                    curr_toks = ""
                    curr_word_ix += 1'''




if __name__ == "__main__":
    main()
