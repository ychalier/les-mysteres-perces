"""
Sha-zoom, an implementation of the audio search algorithm described in the
Computerphile video 'How Shazam Works (Probably!)' published on YouTube on
March 15, 2021 by David Domminney Fowler.
"""

import wave
import matplotlib.pyplot
import numpy
import subprocess
import os
import pickle


def format_timestamp(seconds):
    """
    Format a timestamp in seconds into a string in format hh:mm:ss[:;.]ff
    where frame numbers if truncated.
    """
    return "%02d:%02d:%02d" % (
        int(seconds) // 3600,
        (int(seconds) % 3600) // 60,
        int(seconds) % 60
    )


class ShazoomOptions:

    def __init__(self,
                 chunk_length_ms=100,
                 fft_size=2048,
                 fft_bin_start=4,
                 fft_bin_end=214,
                 fft_bin_step=1,
                 partition_size=6) -> None:
        self.chunk_length_ms = chunk_length_ms
        self.fft_size = fft_size
        self.fft_bin_start = fft_bin_start
        self.fft_bin_end = fft_bin_end
        self.fft_bin_step = fft_bin_step
        self.partition_size = partition_size


class ShazoomDatabase:

    def __init__(self, options):
        self.options = options
        self.tracks = None
        self.labels = None

    def fit(self, tracks, labels, preprocess=False):
        self.tracks = tracks
        if preprocess:
            for track in self.tracks:
                track.preprocess()
        self.labels = labels

    def save_checkpoint(self, path):
        with open(path, "wb") as file:
            pickle.dump({
                "options": self.options,
                "tracks": self.tracks,
                "labels": self.labels
            }, file)

    @classmethod
    def from_checkpoint(cls, path):
        with open(path, "rb") as file:
            checkpoint = pickle.load(file)
        database = cls(checkpoint["options"])
        database.fit(checkpoint["tracks"], checkpoint["labels"])
        return database

    def predict(self, track):
        if self.tracks is None or self.labels is None:
            raise TypeError
        index_max = None
        scores = list()
        for i, ref in enumerate(self.tracks):
            score = track.match(ref)
            scores.append(score)
            if index_max is None or score > scores[index_max]:
                index_max = i
        return {
            "label": self.labels[index_max],
            "score": scores[index_max],
            "confidence": scores[index_max] - max(scores[:index_max] + scores[index_max + 1:]),
            "details": {
                self.labels[i]: score
                for i, score in enumerate(scores)
            }
        }

    def predict_on_the_fly(self, path, temporary_folder, seek=0, duration=15):
        if not os.path.isdir(temporary_folder):
            os.makedirs(temporary_folder)
        track = ShazoomTrack.from_mp3(
            self.options,
            path,
            temporary_folder,
            seek=seek,
            duration=duration
        )
        track.preprocess()
        prediction = self.predict(track)
        os.remove(track.path)
        if len(os.listdir(temporary_folder)) == 0:
            os.rmdir(temporary_folder)
        return prediction


class ShazoomTrack:

    def __init__(self, options, path):
        self.options = options
        self.path = path
        self.framerate = None
        self.waveform = None
        self.fft = None
        self.print = None

    @classmethod
    def from_mp3(cls, options, path, folder, seek=0, duration=15):
        wav_path = os.path.join(
            folder,
            os.path.splitext(os.path.basename(path))[0] + ".wav"
        )
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                format_timestamp(seek),
                "-i",
                path,
                "-t",
                format_timestamp(duration),
                "-ac",
                "1",
                "-acodec",
                "pcm_u8",
                wav_path,
                "-y",
            ],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        process.wait()
        return cls(options, wav_path)

    def _compute_waveform(self):
        spf = wave.open(self.path, "r")
        self.framerate = spf.getframerate()
        self.waveform = list()
        for _ in range(spf.getnframes()):
            frame = spf.readframes(1)
            self.waveform.append(
                (int.from_bytes(frame, byteorder="big") - 128) / 128)
        spf.close()
        return self.waveform, self.framerate

    def _compute_fft(self):
        """
        Use Numpy to compute the Fast Fourier Transform of chunks of a waveform.
        The returned array has shape [
            (fft_bin_end - fft_bin_start) // fft_bin_step,
            nframes / framerate / chunk_length_ms / 1000
        ]
        """
        if self.waveform is None:
            raise TypeError("Waveform is None")
        chunk_length = int(self.framerate / 1000 *
                           self.options.chunk_length_ms)
        chunks = [
            self.waveform[start:start+chunk_length]
            for start in range(0, len(self.waveform), chunk_length)
        ]
        fft = numpy.absolute(numpy.fft.fft(chunks, n=self.options.fft_size)).T
        self.fft = fft[
            self.options.fft_bin_start:self.options.fft_bin_end:self.options.fft_bin_step,
            :
        ]
        return self.fft

    def _compute_print(self):
        """
        Compute the audio print from the FFT.
        Returned array has shape [
            partition_size,
            nframes / framerate / chunk_length_ms / 1000
        ]
        """
        if self.fft is None:
            raise TypeError("FFT is None")
        partition_length = self.fft.shape[0] // self.options.partition_size
        self.print = numpy.zeros(
            (self.options.partition_size, self.fft.shape[1]))
        for j in range(self.fft.shape[1]):
            for i in range(self.options.partition_size):
                partition = self.fft[i *
                                     partition_length:(i+1)*partition_length, j]
                self.print[i, j] = numpy.argmax(partition) + i*partition_length
        return self.print

    def preprocess(self):
        self._compute_waveform()
        self._compute_fft()
        self._compute_print()

    def plot_waveform(self) -> None:
        """
        Plot a waveform.
        """
        matplotlib.pyplot.figure(figsize=(14, 7))
        timeticks = [i / self.framerate for i in range(len(self.waveform))]
        matplotlib.pyplot.plot(timeticks, self.waveform)
        matplotlib.pyplot.xlabel("Time (s)")
        matplotlib.pyplot.ylabel("Amplitude")

    def plot_print(self) -> None:
        """
        Plot the spectrum and the footprint over it.
        """
        partition_size = self.print.shape[0]
        partition_length = self.fft.shape[0] // partition_size
        print_extended = numpy.zeros(self.fft.shape)
        max_val = self.fft.max()
        for i in range(self.fft.shape[0]):
            for j in range(self.fft.shape[1]):
                if i // partition_length == 6:
                    continue
                if self.print[i // partition_length, j] == i:
                    print_extended[i, j] = max_val
        matplotlib.pyplot.figure(figsize=(14, 7))
        matplotlib.pyplot.imshow(
            numpy.maximum(self.fft, print_extended),
            interpolation="nearest",
            aspect="auto",
            origin="lower"
        )
        x_ticks_pos = list(range(
            0,
            self.fft.shape[1] + 1,
            2000 // self.options.chunk_length_ms
        ))
        x_ticks_labels = [
            i * self.options.chunk_length_ms // 1000
            for i in x_ticks_pos
        ]
        matplotlib.pyplot.xticks(ticks=x_ticks_pos, labels=x_ticks_labels)
        matplotlib.pyplot.xlabel("Time (s)")
        y_ticks_pos = list(range(
            0,
            self.fft.shape[0] + 1,
            (self.fft.shape[0] + 1) // 10
        ))
        y_ticks_labels = [
            round(self.framerate / 2 / (self.options.fft_size / 2)
                  * (y + self.options.fft_bin_start) * self.options.fft_bin_step)
            for y in y_ticks_pos
        ]
        matplotlib.pyplot.yticks(ticks=y_ticks_pos, labels=y_ticks_labels)
        matplotlib.pyplot.ylabel("Frequency (Hz)")
        matplotlib.pyplot.tight_layout()

    def match(self, other, match_length=4, look_forward=1):
        if self.print is None:
            raise TypeError("Self.print is None")
        if other.print is None:
            raise TypeError("Other.print is None")
        match_score = 0
        for t_j in range(self.print.shape[1] - look_forward):
            for t_i in range(self.print.shape[0]):
                next_point_groups = []
                for offset in range(match_length):
                    t_ii = t_i + offset
                    t_jj = t_j
                    if t_ii >= self.print.shape[0]:
                        t_ii -= self.print.shape[0]
                        t_jj += 1
                    next_point_groups.append((t_ii, self.print[t_ii, t_jj]))
                if len(next_point_groups) < match_length:
                    continue
                for r_j in range(other.print.shape[1] - look_forward):
                    if self.print[t_i, t_j] == other.print[t_i, r_j]:
                        local_match_score = 0
                        for px in range(match_length):
                            for sx in range(look_forward + 1):
                                if other.print[next_point_groups[px][0], r_j + sx] == next_point_groups[px][1]:
                                    local_match_score += 1
                        if local_match_score >= match_length:
                            match_score += 1
                            break
        return match_score / \
            (self.print.shape[0] * (self.print.shape[1] - look_forward))
