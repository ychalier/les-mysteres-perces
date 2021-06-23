# Les Mystères percés

## Schemas

### [inatheque.json](data/inatheque.json)

- `entries.collection` : string
- `entries.credits.author` : string
- `entries.credits.cast` : array
- `entries.credits.cast.character` : string
- `entries.credits.cast.name` : string
- `entries.credits.crew` : array
- `entries.credits.crew.job` : string
- `entries.credits.crew.name` : string
- `entries.credits.directors` : array
- `entries.credits.directors.name` : string
- `entries.credits.producers` : array
- `entries.credits.producers.name` : string
- `entries.descriptors` : array
- `entries.descriptors.label` : string
- `entries.descriptors.specification` : string
- `entries.diffusion_channel` : string
- `entries.diffusion_date` : string - `YYYY-MM-DD`
- `entries.duration` : int - seconds
- `entries.id` : string
- `entries.production_company` : string
- `entries.recording_date` : string - `YYYY-MM-DD`
- `entries.summary.beginning` : int - seconds
- `entries.summary.end` : int - seconds
- `entries.summary.items` : array
- `entries.summary.items.content` : string
- `entries.summary.items.duration` : int - seconds
- `entries.summary.items.timecode` : int - seconds
- `entries.summary.pitch` : string
- `entries.title` : string
- `entries.uri` : string

### [lmdmfr.json](data/lmdmfr.json)

- `entries.id` : int
- `entries.uri` : string
- `entries.title` : string
- `entries.author` : string
- `entries.diffusion_date` : string - `YYYY-MM-DD`
- `entries.collection` : string
- `entries.creators` : array
- `entries.creators.name` : string

### [youtube.json](data/youtube.json)

- `entries.channel_id` : string
- `entries.channel_name` : string
- `entries.chapters` : array
- `entries.chapters.end` : float - seconds
- `entries.chapters.start` : float - seconds
- `entries.chapters.words` : array
- `entries.chapters.words.label` : string
- `entries.chapters.words.score` : float
- `entries.collection` : string
- `entries.description` : string
- `entries.diffusion_date` : string - `YYYY-MM-DD`
- `entries.duration` : int - seconds
- `entries.facets` : array
- `entries.facets.label` : string
- `entries.facets.score` : int
- `entries.id` : string
- `entries.opening` : string
- `entries.relevant_words` : array
- `entries.relevant_words.label` : string
- `entries.relevant_words.score` : float
- `entries.stats.disklike_count` : int
- `entries.stats.like_count` : int
- `entries.stats.view_count` : int
- `entries.title` : string
- `entries.upload_date` : string - `YYYY-MM-DD`
- `entries.uri` : string
- `entries.video_title` : string

### [madelen.json](data/madelen.json)

- `entries.collection` : string
- `entries.credits.author` : string
- `entries.credits.cast` : array
- `entries.credits.cast.name` : string
- `entries.credits.crew` : array
- `entries.credits.crew.job` : string
- `entries.credits.crew.name` : string
- `entries.credits.directors` : array
- `entries.credits.directors.name` : string
- `entries.credits.producers` : array
- `entries.credits.producers.name` : string
- `entries.descriptors` : array
- `entries.descriptors.label` : string
- `entries.diffusion_date` : string - `YYYY-MM-DD`
- `entries.duration` : int - seconds
- `entries.production_company` : string
- `entries.summary.beginning` : int
- `entries.summary.end` : int - seconds
- `entries.summary.pitch` : string - seconds
- `entries.title` : string
- `entries.uri` : string


### [merger.json](data/merger.json)

- `entries.chapters` : array
- `entries.chapters.end` : float - seconds
- `entries.chapters.start` : float - seconds
- `entries.chapters.words` : array
- `entries.chapters.words.label` : string
- `entries.chapters.words.score` : float
- `entries.collection` : string
- `entries.credits.author` : string
- `entries.credits.cast` : array
- `entries.credits.cast.character` : string
- `entries.credits.cast.name` : string
- `entries.credits.crew` : array
- `entries.credits.crew.job` : string
- `entries.credits.crew.name` : string
- `entries.credits.directors` : array
- `entries.credits.directors.name` : string
- `entries.credits.producers` : array
- `entries.credits.producers.name` : string
- `entries.descriptors` : array
- `entries.descriptors.label` : string
- `entries.descriptors.specification` : string
- `entries.diffusion_date` : string - `YYYY-MM-DD`
- `entries.id` : int
- `entries.duration` : int - seconds
- `entries.facets` : array
- `entries.facets.label` : string
- `entries.facets.score` : int
- `entries.links.inatheque_id` : string
- `entries.links.inatheque_uri` : string
- `entries.links.lmdmfr_id` : int
- `entries.links.lmdmfr_uri` : int
- `entries.links.madelen_uri` : string
- `entries.links.youtube_id` : string
- `entries.links.youtube_uri` : string
- `entries.opening` : string
- `entries.relevant_words` : array
- `entries.relevant_words.label` : string
- `entries.relevant_words.score` : float
- `entries.summary.beginning` : int - seconds
- `entries.summary.end` : int - seconds
- `entries.summary.pitch` : string
- `entries.title` : string

