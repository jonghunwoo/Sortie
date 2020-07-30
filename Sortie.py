import simpy
import random
import statistics
import numpy.random as random
import pandas as pd

wait_times = []
AT_list = []
sortie_times = []
sortie_count = []
sgrlist = []


class Deck_proc(object):
    def __init__(self, env, num_taxing, num_sortie, num_troubleshooting,
                 num_rpr1, num_rpr2, num_rpr3, num_rpr4, num_rpr5,
                 num_turnaround, num_munition_upload):
        self.env = env
        self.taxing = simpy.Resource(env, num_taxing)
        self.sortie = simpy.Resource(env, num_sortie)
        self.troubleshooting = simpy.Resource(env, num_troubleshooting)
        self.rpr1 = simpy.Resource(env, num_rpr1)
        self.rpr2 = simpy.Resource(env, num_rpr2)
        self.rpr3 = simpy.Resource(env, num_rpr3)
        self.rpr4 = simpy.Resource(env, num_rpr4)
        self.rpr5 = simpy.Resource(env, num_rpr5)
        self.turnaround = simpy.Resource(env, num_turnaround)
        self.munition_upload = simpy.Resource(env, num_munition_upload)

    def taxing_fighter(self, fighter):
        yield self.env.timeout(0.25)

    def sortie_fighter(self, fighter):
        yield self.env.timeout(2.00)

    def troubleshooting_fighter(self, fighter):
        yield self.env.timeout(0.5)

    def airframing_fighter(self, fighter):
        yield self.env.timeout(2.2)

    def electrical_fighter(self, fighter):
        yield self.env.timeout(2.27)

    def engine_fighter(self, fighter):
        yield self.env.timeout(2.37)

    def avionics_fighter(self, fighter):
        yield self.env.timeout(1.5)

    def weapons_fighter(self, fighter):
        yield self.env.timeout(1.19)

    def turningaround_fighter(self, fighter):
        yield self.env.timeout(0.75)

    def munition_upload_fighter(self, fighter):
        yield self.env.timeout(0.5)


#############################################################################
def tr_fighting(env, fighter, deck_proc):
    data_1 = [['rpr1', None], ['rpr2', None], ['rpr3', None], ['rpr4', None], ['rpr5', None]]
    probs = [[0.17, 0.83], [0.39, 0.61], [0.21, 0.79], [0.27, 0.73], [0.46, 0.54]]
    parallel_task = [random.choice(data_1[i], p=probs[i]) for i in range(0, 5)]
    if 'rpr1' in parallel_task:
        with deck_proc.rpr1.request() as request:
            yield request
            yield env.process(deck_proc.airframing_fighter(fighter))
    if 'rpr2' in parallel_task:
        with deck_proc.rpr2.request() as request:
            yield request
            yield env.process(deck_proc.electrical_fighter(fighter))
    if 'rpr3' in parallel_task:
        with deck_proc.rpr3.request() as request:
            yield request
            yield env.process(deck_proc.engine_fighter(fighter))
    if 'rpr4' in parallel_task:
        with deck_proc.rpr4.request() as request:
            yield request
            yield env.process(deck_proc.avionics_fighter(fighter))
    if 'rpr5' in parallel_task:
        with deck_proc.rpr5.request() as request:
            yield request
            yield env.process(deck_proc.weapons_fighter(fighter))
    with deck_proc.turnaround.request() as request:
        yield request
        yield env.process(deck_proc.turningaround_fighter(fighter))

    with deck_proc.munition_upload.request() as request:
        yield request
        yield env.process(deck_proc.munition_upload_fighter(fighter))


#############################################################################
def Fighter_proc(env, fighter, deck_proc):
    arrival_time = env.now
    fighter = 0

    with deck_proc.taxing.request() as request:
        yield request
        yield env.process(deck_proc.taxing_fighter(fighter))

    choice = random.choice(['sortie', 'troubleshooting'], p=[0.95, 0.05])
    if choice == 'sortie':
        with deck_proc.sortie.request() as request:
            yield request
            fighter += 1
            sortie_count.append(fighter)
            sgr = (len(sortie_count) + 1) / env.now
            sgrlist.append(sgr)
            yield env.process(deck_proc.sortie_fighter(fighter))
            choice = random.choice(['turnaround', 'troubleshooting'], p=[0.7, 0.3])
            if choice == 'turnaround':
                with deck_proc.turnaround.request() as request:
                    yield request
                    yield env.process(deck_proc.turningaround_fighter(fighter))
                with deck_proc.munition_upload.request() as request:
                    yield request
                    yield env.process(deck_proc.munition_upload_fighter(fighter))
            else:
                env.process(tr_fighting(env, fighter, deck_proc))
    else:
        env.process(tr_fighting(env, fighter, deck_proc))

    wait_times.append(env.now - arrival_time)


#############################################################################
def run_sortie(env, num_taxing, num_sortie, num_troubleshooting,
               num_rpr1, num_rpr2, num_rpr3, num_rpr4, num_rpr5,
               num_turnaround, num_munition_upload):
    deck_proc = Deck_proc(env, num_taxing, num_sortie, num_troubleshooting,
                          num_rpr1, num_rpr2, num_rpr3, num_rpr4, num_rpr5,
                          num_turnaround, num_munition_upload)

    schedule = pd.read_csv('C:\\Users\\DMOS\\Downloads\\schedule.csv')
    schedule_df = pd.DataFrame(schedule)
    fighter = 0
    inter_arrival_list = [schedule_df.iloc[i][1] - schedule_df.iloc[i - 1][1] for i in range(1, len(schedule_df))]
    inter_arrival_list.insert(0, 1)
    for i in inter_arrival_list:
        yield env.timeout(i)
        fighter += 1
        AT_list.append(env.now)
        env.process(Fighter_proc(env, fighter, deck_proc))


def main():
    env = simpy.Environment()
    env.process(run_sortie(env, 1000, 1000, 1000, 1, 3, 2, 1, 2, 6, 4))
    env.run(until=200)
    c = zip(AT_list, sgrlist)
    d = pd.DataFrame(c, columns=['Arrival Rate', 'SGR'])
    print(d)


main()