# Les Mystères percés

## Schemas

### [inatheque.json](data/inatheque.json)

- `entries.id` : string
- `entries.uri` : string
- `entries.title` : string
- `entries.collection` : string
- `entries.diffusion_channel` : string
- `entries.diffusion_date` : string - YYYY-MM-DD
- `entries.recording_date` : string - YYYY-MM-DD
- `entries.duration` : int - seconds
- `entries.production_company` : string
- `entries.descriptors` : array
- `entries.descriptors.label` : string
- `entries.descriptors.specification` : string
- `entries.credits.author` : string
- `entries.credits.directors` : array
- `entries.credits.directors.name` : string
- `entries.credits.producers` : array
- `entries.credits.producers.name` : string
- `entries.credits.cast` : array
- `entries.credits.cast.name` : string
- `entries.credits.cast.character` : string
- `entries.credits.crew` : array
- `entries.credits.crew.name` : string
- `entries.credits.crew.job` : string
- `entries.summary.pitch` : string
- `entries.summary.beginning` : int
- `entries.summary.end` : int
- `entries.summary.items` : array
- `entries.summary.items.timecode` : int
- `entries.summary.items.duration` : int
- `entries.summary.items.text` : string

### [lmdmfr.json](data/lmdmfr.json)

- `entries.id` : int
- `entries.uri` : string
- `entries.title` : string
- `entries.author` : string
- `entries.diffusion_date` : string - YYYY-MM-DD
- `entries.collection` : string
- `entries.creators` : array
- `entries.creators.name` : string

### [youtube.json](data/youtube.json)

- `entries.id` : string
- `entries.uri` : string
- `entries.channel_id` : string
- `entries.channel_name` : string
- `entries.video_title` : string
- `entries.title` : string
- `entries.collection` : string
- `entries.upload_date` : string - YYYY-MM-DD
- `entries.duration` : int
- `entries.stats.view_count` : int
- `entries.stats.like_count` : int
- `entries.stats.disklike_count` : int
- `entries.description` : string
- `entries.opening` : string
- `entries.diffusion_date` : string - YYYY-MM-DD
- `entries.facets` : array
- `entries.facets.label` : string
- `entries.facets.score` : int
- `entries.relevant_words` : array
- `entries.relevant_words.label` : string
- `entries.relevant_words.score` : float
- `entries.chapters` : array
- `entries.chapters.start` : float
- `entries.chapters.end` : float
- `entries.chapters.words` : array
- `entries.chapters.words.label` : string
- `entries.chapters.words.score` : float

### [madelen.json](data/madelen.json)

- `entries.uri` : string
- `entries.title` : string
- `entries.collection` : string
- `entries.diffusion_date` : string - YYYY-MM-DD
- `entries.production_company` : string
- `entries.descriptors` : array
- `entries.descriptors.label` : string
- `entries.duration` : int
- `entries.summary.pitch` : string
- `entries.summary.beginning` : int
- `entries.summary.end` : int
- `entries.descriptors` : array
- `entries.descriptors.label` : string
- `entries.credits.author` : string
- `entries.credits.directors` : array
- `entries.credits.directors.name` : string
- `entries.credits.producers` : array
- `entries.credits.producers.name` : string
- `entries.credits.cast` : array
- `entries.credits.cast.name` : string
- `entries.credits.crew` : array
- `entries.credits.crew.name` : string
- `entries.credits.crew.job` : string

### [merger.json](data/merger.json)

- `entries.id` : int
- `entries.inatheque_id` : string
- `entries.inatheque_uri` : string
- `entries.lmdmfr_id` : int
- `entries.lmdmfr_uri` : int
- `entries.madelen_uri` : string
- `entries.youtube_id` : string
- `entries.youtube_uri` : string
- `entries.opening` : string
- `entries.title` : string
- `entries.collection` : string
- `entries.diffusion_date` : string - YYYY-MM-DD
- `entries.duration` : int - seconds
- `entries.descriptors` : array
- `entries.descriptors.label` : string
- `entries.descriptors.specification` : string
- `entries.facets` : array
- `entries.facets.label` : string
- `entries.facets.score` : int
- `entries.credits.author` : string
- `entries.credits.directors` : array
- `entries.credits.directors.name` : string
- `entries.credits.producers` : array
- `entries.credits.producers.name` : string
- `entries.credits.cast` : array
- `entries.credits.cast.name` : string
- `entries.credits.cast.character` : string
- `entries.credits.crew` : array
- `entries.credits.crew.name` : string
- `entries.credits.crew.job` : string
- `entries.pitch` : string
- `entries.beginning` : int
- `entries.end` : int
- `entries.chapters` : array
- `entries.chapters.start` : float
- `entries.chapters.end` : float
- `entries.chapters.words` : array
- `entries.chapters.words.label` : string
- `entries.chapters.words.score` : float
