import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.Map.Entry;


public class amazonData {

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
	
	static class Rating {
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
	}
}
