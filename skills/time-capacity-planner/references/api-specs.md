# Time capacity planner interface

The consumer passes a `capacity_profile` containing timezone, fixed events,
work/review/flexible periods, difficulty mapping, and override rules. Each
planned item returns an ID, status, owner, estimated periods, dependencies,
target period, evidence requirement, and confidence. A plan never grants
permission to create or change an external task or event.
