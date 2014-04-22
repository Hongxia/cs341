import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.Map.Entry;


public class amazonData {

	static int NUM_EXPERIENCE_LEVEL = 5;
	
	public static void main(String[] args) {
		for (int i = 0; i < args.length; i++) {
			System.out.println(args[i]);
		}
		if (args.length != 1) {
			System.out.println("Usage: java amazonData <filename>");
			System.exit(-1);
		}
		HashMap<String, ArrayList<Rating> > ratingsMap = readFile(args[0]);
		if (ratingsMap == null) {
			System.out.println("Map could not be created");
			System.exit(-1);
		}
		doStuff(ratingsMap);
		HashMap<String, ArrayList<ArrayList<Rating>>> ratingsMapBucket = makeExpBuckets(ratingsMap); 
		doStuffBucketed(ratingsMapBucket);
	}
	
	private static void doStuffBucketed(
			HashMap<String, ArrayList<ArrayList<Rating>>> ratingsMapBucket) {
		SimpleDateFormat sdf = new SimpleDateFormat("MM/dd/yyyy HH:mm");
		for (Entry<String, ArrayList<ArrayList<Rating>>> entry : ratingsMapBucket.entrySet()) {
			ArrayList<ArrayList<Rating>> bucketedRatings = entry.getValue();
			// Only print for users which have at least 3 ratings in exp level 5, which 
			// means they have at least 15 ratings total
			if (bucketedRatings.get(4).size() < 3) continue;
			System.out.println("User: " + entry.getKey());
			for (int i = 0; i < NUM_EXPERIENCE_LEVEL; i++) {
				ArrayList<Rating> ratings = bucketedRatings.get(i);
				if (ratings.size() == 0) {
					System.out.println("Experience level " + (i + 1) + " has no reviews");
				} else {
					int numReviewsSoFar = ratings.size() * i;
					System.out.println("Experience level " + (i + 1) + " after " + numReviewsSoFar + " reviews");
					Rating r = ratings.get(0);
					System.out.println("Starts at time: " + sdf.format(r.getTime()));
				}				
			}
			System.out.println();
		}
		
	}

	private static HashMap<String, ArrayList<ArrayList<Rating>>> makeExpBuckets(
			HashMap<String, ArrayList<Rating>> ratingsMap) {
		HashMap<String, ArrayList<ArrayList<Rating>>> ratingsMapBucket = new HashMap<String, ArrayList<ArrayList<Rating>>>();
		for (Entry<String, ArrayList<Rating> > entry : ratingsMap.entrySet()) {
			ArrayList<Rating> ratings = entry.getValue();
			Collections.sort(ratings);
			// The integer index which represents 1/5 of the ratings of this user.
			int indFraction = ratings.size() / NUM_EXPERIENCE_LEVEL;
			
			ArrayList<ArrayList<Rating>> bucketed = new ArrayList<ArrayList<Rating>>();
			
			for (int i = 0; i < NUM_EXPERIENCE_LEVEL; i++) {
				ArrayList<Rating> expBucket = new ArrayList<Rating>(); 
				for (int j = i*indFraction; j < (i+1)*indFraction ; j++) {
					expBucket.add(ratings.get(j));
				}
				bucketed.add(expBucket);
			}
			
			ratingsMapBucket.put(entry.getKey(), bucketed);
		}
		return ratingsMapBucket;
	}

	private static HashMap<String, ArrayList<Rating> > readFile(String filename) {
		BufferedReader br = null;
		try { 
			String curLine;
			br = new BufferedReader(new FileReader(filename));
			HashMap<String, ArrayList<Rating> > ratingsMap = new HashMap<String, ArrayList<Rating> >(); 
			while ((curLine = br.readLine()) != null) {
				String[] splitted = curLine.split(",");
				String pid = splitted[0];
				String uid = splitted[1];
				double rating = Double.parseDouble(splitted[2]);
				// Multiply because Date constructor requires milliseconds past 1970
				Date t = new Date(Long.parseLong(splitted[3]) * 1000L);
				Rating r = new Rating(pid, rating, t);
				
				if (!ratingsMap.containsKey(uid)) ratingsMap.put(uid, new ArrayList<Rating>());
				ratingsMap.get(uid).add(r);
			}
			return ratingsMap; 
		} catch (IOException e) {
			e.printStackTrace();
		} finally {
			try {
				if (br != null) br.close();
			} catch (IOException ex) {
				ex.printStackTrace();
			}
		}
		return null;
	}
	
	private static void doStuff(HashMap<String, ArrayList<Rating> > ratingsMap) {
		System.out.println("Performing analysis on the user ratings");
		System.out.println("Num users: " + ratingsMap.size());
		Date firstRating = null;
		Date lastRating = null;
		int maxRatingsByUser = -1;
		int minRatingsByUser = -1;
		int totalRatings = 0;
		for (Entry<String, ArrayList<Rating> > entry : ratingsMap.entrySet()) {
			ArrayList<Rating> ratings = entry.getValue();
			totalRatings += ratings.size();
			if (maxRatingsByUser == -1 || ratings.size() > maxRatingsByUser) {
				maxRatingsByUser = ratings.size();
			}
			if (minRatingsByUser == -1 || ratings.size() < minRatingsByUser) {
				minRatingsByUser = ratings.size();
			}
			for (int i = 0; i < ratings.size(); i++) {
				Date d = ratings.get(i).getTime();
				if (firstRating == null || d.before(firstRating)) firstRating = d;
				
				if (lastRating == null || d.after(lastRating)) lastRating = d;
			}
		}
		System.out.println("Total number of ratings: " + totalRatings);
		System.out.println("Max number ratings by user: " + maxRatingsByUser);
		System.out.println("Min number ratings by user: " + minRatingsByUser);
		
		SimpleDateFormat sdf = new SimpleDateFormat("MM/dd/yyyy HH:mm");
		System.out.println("Date of first rating: " + sdf.format(firstRating));
		System.out.println("Date of last rating: " + sdf.format(lastRating));
	}
	
	static class Rating implements Comparable<Rating> {
		private String pid; // Product ID
		private double rating; // User rating
		private Date time; // Time of rating
		
		public Rating(String pid, double rating, Date time) {
			this.setPid(pid);
			this.setRating(rating);
			this.setTime(time);
		}
		public Date getTime() {
			return time;
		}
		public void setTime(Date time) {
			this.time = time;
		}
		public double getRating() {
			return rating;
		}
		public void setRating(double rating) {
			this.rating = rating;
		}
		public String getPid() {
			return pid;
		}
		public void setPid(String pid) {
			this.pid = pid;
		}
		
		@Override
		public int compareTo(Rating r) {
			return (this.time).compareTo(r.getTime());
		}
	}
}
